# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_validity_date(self):
        return super(SaleOrder, self)._default_validity_date()
    
    def _get_default_require_signature(self):
        return super(SaleOrder, self)._get_default_require_signature()

    def _get_default_require_payment(self):
        return super(SaleOrder, self)._get_default_require_payment()
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('pending_approval', 'Pending Approval'),
                                        ('pending_ff_approval', 'Pending Fulfillment Approval'),
                                        ('draft', 'Quotation'),
                                        ('sent', 'Quotation Sent'),
                                        ('sale', 'Sales Order'),
                                        ('done', 'Locked'),
                                        ('cancel', 'Cancelled'),],
                             string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)],
                               'new': [('readonly', False)],
                               'pending_approval': [('readonly', False)],
                               'pending_ff_approval': [('readonly', False)]},
                       index=True, default=lambda self: _('New'))
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)],
                                         'new': [('readonly', False)],
                                         'pending_approval': [('readonly', False)],
                                         'pending_ff_approval': [('readonly', False)]},
                                 copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration', readonly=True, copy=False,
                                states={'draft': [('readonly', False)],
                                        'sent': [('readonly', False)],
                                        'new': [('readonly', False)],
                                        'pending_approval': [('readonly', False)],
                                        'pending_ff_approval': [('readonly', False)]},
                                default=_default_validity_date)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, readonly=True,
                                       states={'draft': [('readonly', False)],
                                               'sent': [('readonly', False)],
                                               'new': [('readonly', False)],
                                               'pending_approval': [('readonly', False)],
                                               'pending_ff_approval': [('readonly', False)]},
                                       help='Request a online signature to the customer in order to confirm orders automatically.')
    require_payment = fields.Boolean('Online Payment', default=_get_default_require_payment, readonly=True,
                                     states={'draft': [('readonly', False)],
                                             'sent': [('readonly', False)],
                                             'new': [('readonly', False)],
                                             'pending_approval': [('readonly', False)],
                                             'pending_ff_approval': [('readonly', False)]},
                                     help='Request an online payment to the customer in order to confirm orders automatically.')

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)],
                                         'new': [('readonly', False)],
                                         'pending_approval': [('readonly', False)],
                                         'pending_ff_approval': [('readonly', False)]},
                                 required=True, change_default=True, index=True, tracking=1,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address',
                                         readonly=True, required=True,
                                         states={'draft': [('readonly', False)],
                                                 'sent': [('readonly', False)],
                                                 'sale': [('readonly', False)],
                                                 'new': [('readonly', False)],
                                                 'pending_approval': [('readonly', False)],
                                                 'pending_ff_approval': [('readonly', False)]},
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'sale': [('readonly', False)],
                                                  'new': [('readonly', False)],
                                                  'pending_approval': [('readonly', False)],
                                                  'pending_ff_approval': [('readonly', False)]},
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)],
                                           'sent': [('readonly', False)],
                                           'new': [('readonly', False)],
                                           'pending_approval': [('readonly', False)],
                                           'pending_ff_approval': [('readonly', False)]},
                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                   help="If you change the pricelist, only newly added lines will be affected.")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          readonly=True, copy=False, check_company=True,  # Unrequired company
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'new': [('readonly', False)],
                                                  'pending_approval': [('readonly', False)],
                                                  'pending_ff_approval': [('readonly', False)]},
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          help="The analytic account related to a sales order.")

    commitment_date = fields.Datetime('Delivery Date',
                                      states={'draft': [('readonly', False)],
                                              'sent': [('readonly', False)],
                                              'new': [('readonly', False)],
                                              'pending_approval': [('readonly', False)],
                                              'pending_ff_approval': [('readonly', False)]},
                                      copy=False, readonly=True,
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    
    
    def _write(self, values):
        """ Override of private write method in order to generate activities
        based in the invoice status. As the invoice status is a computed field
        triggered notably when its lines and linked invoice status changes the
        flow does not necessarily goes through write if the action was not done
        on the SO itself. We hence override the _write to catch the computation
        of invoice_status field. """
        if self.env.context.get('mail_activity_automation_skip'):
            return super(SaleOrder, self)._write(values)

        if 'invoice_status' in values:
            if values['invoice_status'] == 'upselling':
                filtered_self = self.search([('id', 'in', self.ids),
                                             ('user_id', '!=', False),
                                             ('invoice_status', '!=', 'upselling')])
                filtered_self.activity_unlink(['sale.mail_act_sale_upsell'])
                for order in filtered_self:
                    order.activity_schedule(
                        'sale.mail_act_sale_upsell',
                        user_id=order.user_id.id,
                        note=_("Upsell <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer <a href='#' data-oe-model='%s' data-oe-id='%s'>%s</a>") % (
                            order._name, order.id, order.name,
                            order.partner_id._name, order.partner_id.id, order.partner_id.display_name))
                    
        # Set the sale order status to new if any of the order line is
        new_status = False
        active_id = None
        if self.env.context.get('active_id'):
            active_id = self.env.context['active_id']
        elif len(self.ids) == 1:
            active_id = self.ids[0]
        
        if active_id and 'state' not in values:
            vals = dict(values).copy()
            # this should be done only for the current order 
            # that's being actively updated
            sale_order = self.env['sale.order'].sudo().browse(active_id)
            
            # continue only if the sale order is not in new already
            curr_state = self.env.cr.execute("SELECT state FROM sale_order WHERE id = {0}".format(active_id))
            if curr_state != 'new':
                for sol in sale_order.order_line:
                    if sol.state == 'new':
                        new_status = True
            
                if new_status:
                    vals['state'] = 'new'
                    sale_order.track_state_change(vals['state'])
                    return super(SaleOrder, sale_order)._write(vals)
            
        # Track the state changes - pending ff approval/pending approval
        if 'state' in values:
            self.track_state_change(values['state'])
    
        return super(SaleOrder, self)._write(values)
   
    def track_state_change(self, new_value):
        """
        Track the state change for the current sale order. This is 
        added since the _write method called to do updates doesn't track 
        the state changes and hence are not logged to the chatter.
        NOTE: For now we are tracking just state change here since
        thats the only field being updated forcefully.
        """
        
        state_fld = self.env['sale.order'].fields_get()['state']
        old_value = [x[1] for x in state_fld['selection'] if x[0] == self.state][0]
        new_value = [x[1] for x in state_fld['selection'] if x[0] == new_value][0]
        if new_value != old_value:
            tracking_dict = {'field_name': state_fld['string'], 
                             'old_value': old_value,
                             'new_value': new_value,
                            }
            msg = self._get_tracking_field_string([tracking_dict])
            # skip if the message was already posted
            now = datetime.now()
            from_t = datetime.strftime(now - relativedelta(seconds=1), '%Y-%m-%d %H:%M:%S.0')
            to_t = datetime.strftime(now + relativedelta(seconds=1), '%Y-%m-%d %H:%M:%S.0')
            mail_msg = self.env['mail.message'].search([('model', '=', 'sale.order'), 
                                                        ('res_id', '=', self.ids[0]),
                                                        ('body', '=', msg), 
                                                        ('write_date', '>=', from_t), 
                                                        ('write_date', '<=', to_t)])
            if not mail_msg:
                self.message_post(body=msg)

    def _get_tracking_field_string(self, fields):
        """
        Frame the message to be logged in the chatter.
        """
        
        ARROW_RIGHT = '<span class="fa fa-long-arrow-right" title="Changed"></span>'
        msg = '<ul>'
        for field in fields:
            if field.get('error', False):
                msg += '<li>%s: %s</li>' % (
                    field['field_error'],
                    _('A modification has been operated on the line %s.', redirect_link)
                )
            else:
                msg += '<li>%s: %s %s %s</li>' % (field['field_name'], field['old_value'], ARROW_RIGHT, field['new_value'])
        msg += '</ul>'
        return msg

    def _get_allowed_state_approve(self):
        return {'pending_approval', 'pending_ff_approval'}

    def action_approve_price_approval(self):
        self.action_approve()

    def action_approve_ff_approval(self):
        self.action_approve()

    def action_approve(self):
        """
        Method to approve a sale order
        thats in pending approval or 
        pending ff approval
        """
        
        if not (self._get_allowed_state_approve() & set(self.mapped('state'))):
            raise UserError(_(
                'It is not allowed to approve an order if not in the following states: %s'
            ) % (', '.join(self._get_allowed_state_approve())))
            
        # Update the order line status
        # get the active sale order record
        so_state = 'draft'
        for sol in self.order_line:
            is_ff_approved = True
            is_price_approved = True
            requires_ff_approval = False
            requires_price_approval = False
            if sol.state in self._get_allowed_state_approve():
                # if requires ff approval, then check if the price was changed and 
                # go for sales manager approval
                if sol.product_id.requires_ff_approval and sol.requires_ff_approval:
                    is_ff_approved = True
                    if sol.requires_price_approval:
                        product = sol.product_id.with_context(lang=get_lang(self.env, self.partner_id.lang).code,
                                                                partner=self.partner_id,
                                                                quantity=sol.product_uom_qty,
                                                                date=self.date_order,
                                                                pricelist=self.pricelist_id.id,
                                                                uom=sol.product_uom.id
                        )

                        price_unit = self.env['account.tax']._fix_tax_included_price_company(sol._get_display_price(product), product.taxes_id, sol.tax_id, sol.company_id)

                        # if the price is manually changed
                        so_state = 'pending_approval'
                        requires_price_approval = True
                        is_price_approved = False

                elif self.state == 'pending_ff_approval' and sol.state == 'pending_approval':
                    # if sale order was ff approved, now move it to pending price approval
                    so_state = 'pending_approval'
                    requires_price_approval = True
                    is_price_approved = False
                    
                else:
                    is_price_approved = True
                    is_ff_approved = True
                              
                sol.write({'state': so_state, 
                           'is_ff_approved': is_ff_approved,
                           'is_price_approved': is_price_approved,
                           'requires_ff_approval': requires_ff_approval,
                           'requires_price_approval': requires_price_approval})
          
        ret = self._write({'state': so_state})
        self.send_notification_email(so_state)
        return ret


    def request_approval(self):
        """
        Method to move the sale order
        to pending approval or 
        pending ff approval
        """
        
        if self.state not in ('new'):
            raise UserError(_(
                'It is not allowed to request an approval on this order'
            ))
            
        so_state = None
        # get the active sale order record
        for sol in self.order_line:
            sol_state = None
            if sol.state == 'new':
                if sol.product_id.requires_ff_approval:
                    so_state = sol_state = 'pending_ff_approval'
                else:
                    sol_state = 'pending_approval'
                    if so_state != 'pending_ff_approval':
                        so_state = 'pending_approval'
                
                if sol_state:
                    sol.write({'state': sol_state})
        
        vals = {}
        if so_state:
            vals['state'] = so_state
            ret = self._write(vals)
            self.send_notification_email(so_state)
            return ret

        
    def send_notification_email(self, so_state):
        """
        Send out the notification email
        on state change.
        """
        
        mail_template = None
        if so_state == 'pending_approval':
            mail_template = self.env['mail.template'].search([('name', '=', 'Quotation Pending Approval'),
                                                              ('model', '=', 'sale.order'),
                                                            ])

        elif so_state == 'pending_ff_approval':
            mail_template = self.env['mail.template'].search([('name', '=', 'Notify Fulfillment Manager of Fulfillment Approval Required'),
                                                              ('model', '=', 'sale.order'),
                                                            ])

        if mail_template:
            # Set force_send to true to send the email out immediately
            mail_id = mail_template.send_mail(self.ids[0], force_send=True)
            return True
            
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    state = fields.Selection([('new', 'New'),
                              ('pending_approval', 'Pending approval'),
                              ('pending_ff_approval', 'Pending Fulfillment Approval'),
                              ('ff_approved', 'Fulfillment Approved'),
                              ('draft', 'Quotation'),
                              ('sent', 'Quotation Sent'),
                              ('sale', 'Sales Order'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled'),],
                              string='Order Status', related='order_id.state', copy=False, store=True, default='draft', readonly=True)

    requires_ff_approval = fields.Boolean('Requires Fulfillment approval', default=False, store=True,
                                          compute="_check_requires_ff_approval", help='Determines if the product requires approval by fulfillment')
    
    requires_price_approval = fields.Boolean('Requires Price approval', default=False, store=True,
                                             compute="_check_requires_price_approval", help='Determines if the product requires price approval')

    is_ff_approved = fields.Boolean('Is Fulfillment approved', default=True, store=True,
                                    help='Determines if the product is already approved by fulfillment')
    
    is_price_approved = fields.Boolean('Is Price approved', default=True, store=True,
                                        help='Determines if the product price change is already approved')
    
    def init(self):
        # Set a value on existing records for default values
        for column_name, value in [('is_ff_approved', 't'),
                                   ('is_price_approved', 't'),
                                   ('requires_ff_approval', 'f'),
                                   ('requires_price_approval', 'f')]:
            self.env.cr.execute("UPDATE sale_order_line SET {0} = '{1}' WHERE {0} IS NULL".format(column_name, value))
        
    @api.depends('product_id')
    def _check_requires_ff_approval(self):
        for each in self:
            each.requires_ff_approval = False
            each.is_ff_approved = True

            if not each.product_id:
                return
        
            if each.product_id.requires_ff_approval:
                each.requires_ff_approval = True
                each.is_ff_approved = False

    
    @api.depends('price_unit', 'discount')
    def _check_requires_price_approval(self):
        for each in self:
            each.requires_price_approval = False
            each.is_price_approved = True
            
            if not each.product_id:
                return

            if each.state != 'pending_approval' and each.order_id.pricelist_id and each.order_id.partner_id:
                    product = each.product_id.with_context(lang=get_lang(self.env, each.order_id.partner_id.lang).code,
                                                            partner=each.order_id.partner_id,
                                                            quantity=each.product_uom_qty,
                                                            date=each.order_id.date_order,
                                                            pricelist=each.order_id.pricelist_id.id,
                                                            uom=each.product_uom.id
                    )
                    price_unit = self.env['account.tax']._fix_tax_included_price_company(each._get_display_price(product), product.taxes_id, each.tax_id, each.company_id)
                    # if the price is manually changed
                    if price_unit != each.price_unit:
                        each.requires_price_approval = True
                        each.is_price_approved = False

            if each.discount:
                each.requires_price_approval = True
                each.is_price_approved = False
    
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a sale order line. Instead you should delete the current line and create a new line of the proper type."))

        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) != 0)._update_line_quantity(values)

        # Prevent writing on a locked SO.
        protected_fields = self._get_protected_fields()
        if 'done' in self.mapped('order_id.state') and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))
            fields = self.env['ir.model.fields'].search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            raise UserError(
                _('It is forbidden to modify the following fields in a locked order:\n%s')
                % '\n'.join(fields.mapped('field_description'))
            )

        vals = dict(values).copy()
        # if state not being updated here and if the state is not locked/cancelled, then check
        # for the product ff approval and price approval
        if 'state' not in vals and self.state not in ('done', 'cancelled'):
            if self.product_id.requires_ff_approval and self.state != 'pending_ff_approval' and self.requires_ff_approval is True:
                # if product requires ff approval
                vals['state'] = 'new'
                vals['requires_ff_approval'] = True
                vals['is_ff_approved'] = False

            if self.state != 'pending_approval' and self.requires_price_approval is True:
                # if the price is manually changed
                vals['state'] = 'new'
                vals['requires_price_approval'] = True
                vals['is_price_approved'] = False
                        
        return super(SaleOrderLine, self).write(vals)
    
