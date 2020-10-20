# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False
    
    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign

    def _get_default_require_payment(self):
        return self.env.company.portal_confirmation_pay
    
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
                               'pending_approval': [('readonly', False)],
                               'pending_ff_approval': [('readonly', False)]},
                       index=True, default=lambda self: _('New'))
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)],
                                         'pending_approval': [('readonly', False)],
                                         'pending_ff_approval': [('readonly', False)]},
                                 copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration', readonly=True, copy=False,
                                states={'draft': [('readonly', False)],
                                        'sent': [('readonly', False)],
                                        'pending_approval': [('readonly', False)],
                                        'pending_ff_approval': [('readonly', False)]},
                                default=_default_validity_date)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, readonly=True,
                                       states={'draft': [('readonly', False)],
                                               'sent': [('readonly', False)],
                                               'pending_approval': [('readonly', False)],
                                               'pending_ff_approval': [('readonly', False)]},
                                       help='Request a online signature to the customer in order to confirm orders automatically.')
    require_payment = fields.Boolean('Online Payment', default=_get_default_require_payment, readonly=True,
                                     states={'draft': [('readonly', False)],
                                             'sent': [('readonly', False)],
                                             'pending_approval': [('readonly', False)],
                                             'pending_ff_approval': [('readonly', False)]},
                                     help='Request an online payment to the customer in order to confirm orders automatically.')

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)],
                                         'pending_approval': [('readonly', False)],
                                         'pending_ff_approval': [('readonly', False)]},
                                 required=True, change_default=True, index=True, tracking=1,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address',
                                         readonly=True, required=True,
                                         states={'draft': [('readonly', False)],
                                                 'sent': [('readonly', False)],
                                                 'sale': [('readonly', False)],
                                                 'pending_approval': [('readonly', False)],
                                                 'pending_ff_approval': [('readonly', False)]},
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'sale': [('readonly', False)],
                                                  'pending_approval': [('readonly', False)],
                                                  'pending_ff_approval': [('readonly', False)]},
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)],
                                           'sent': [('readonly', False)],
                                           'pending_approval': [('readonly', False)],
                                           'pending_ff_approval': [('readonly', False)]},
                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                   help="If you change the pricelist, only newly added lines will be affected.")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          readonly=True, copy=False, check_company=True,  # Unrequired company
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'pending_approval': [('readonly', False)],
                                                  'pending_ff_approval': [('readonly', False)]},
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          help="The analytic account related to a sales order.")

    commitment_date = fields.Datetime('Delivery Date',
                                      states={'draft': [('readonly', False)],
                                              'sent': [('readonly', False)],
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
        sale_order = self.env['sale.order'].sudo().browse(self.ids)
        new_status = False
        pricelist = self.env['product.pricelist']
        for sol in sale_order.order_line:
            if sol.state == 'new':
                new_status = True
            
        vals = dict(values).copy()
        if new_status:
            vals['state'] = 'new'
            _logger.warning("Updating sale order to 'new' status - {0}".format(vals))
        
        return super(SaleOrder, self)._write(vals)

    def _get_allowed_state_approve(self):
        return {'pending_approval', 'pending_ff_approval'}

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
        so_state = 'draft'
        for sol in self.order_line:
            if sol.state in self._get_allowed_state_approve():
                # if requires ff approval, then check if the price was changed and 
                # go for sales manager approval
                if sol.product_id.requires_ff_approval and sol.state != 'pending_approval':
                    if self.pricelist_id and self.partner_id:
                        product = sol.product_id.with_context(lang=get_lang(self.env, self.partner_id.lang).code,
                                                                partner=self.partner_id,
                                                                quantity=sol.product_uom_qty,
                                                                date=self.date_order,
                                                                pricelist=self.pricelist_id.id,
                                                                uom=sol.product_uom.id
                        )

                        price_unit = self.env['account.tax']._fix_tax_included_price_company(sol._get_display_price(product), product.taxes_id, sol.tax_id, sol.company_id)

                        # if the price is manually changed
                        if price_unit != sol.price_unit:
                            so_state = 'pending_approval'
                            _logger.warning("Product price changed from {0} to {1}. Setting to pending approval".format(price_unit, sol.price_unit))

                elif self.state == 'pending_ff_approval' and sol.state == 'pending_approval':
                    # if sale order was ff approved, now move it to pending price approval
                    so_state = 'pending_approval'
                
                sol._write({'state': so_state})
                
        self._write({'state': so_state})

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
            _logger.warning("Updating sale order - {0}".format(vals))
            return self._write(vals)    
            

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
                             related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    
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
        # if state not being updated here, then check
        # for the product ff approval and price approval
        if 'state' not in vals:
            if self.product_id.requires_ff_approval and self.state != 'pending_ff_approval':
                # if product requires ff approval
                vals['state'] = 'new'
            else:
                if self.state != 'pending_approval' and self.order_id.pricelist_id and self.order_id.partner_id:
                    product = self.product_id.with_context(lang=get_lang(self.env, self.order_id.partner_id.lang).code,
                                                            partner=self.order_id.partner_id,
                                                            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                                                            date=self.order_id.date_order,
                                                            pricelist=self.order_id.pricelist_id.id,
                                                            uom=self.product_uom.id
                    )

                    price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

                    # if the price is manually changed
                    if price_unit != self.price_unit:
                        vals['state'] = 'new'
            
        result = super(SaleOrderLine, self).write(vals)
        return result

