# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Company(models.Model):
    _inherit = 'res.company'

    sale_quatation_template = fields.Many2one('mail.template', string="Sale Quotation Template")
    sale_order_template = fields.Many2one('mail.template', string="Sale Order Template")
    purchase_quatation_template = fields.Many2one('mail.template', string="Purchase Quotation Template")
    purchase_order_template = fields.Many2one('mail.template', string="Purchase Order Template")
    invoice_template = fields.Many2one('mail.template', string="Invoice Template:")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_quatation_template = fields.Many2one(related='company_id.sale_quatation_template', string="Sale Quotation Template", readonly=False)
    sale_order_template = fields.Many2one(related='company_id.sale_order_template', string="Sale Order Template", readonly=False)
    purchase_quatation_template = fields.Many2one(related='company_id.purchase_quatation_template', string="Purchase Quotation Template", readonly=False)
    purchase_order_template = fields.Many2one(related='company_id.purchase_order_template', string="Template", readonly=False)
    invoice_template = fields.Many2one(related='company_id.invoice_template', string="Purchase Order Template", readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sale_quatation_template = ICPSudo.get_param('generic_default_email_template_app.sale_quatation_template')
        sale_order_template = ICPSudo.get_param('generic_default_email_template_app.sale_order_template')
        purchase_quatation_template = ICPSudo.get_param('generic_default_email_template_app.purchase_quatation_template')
        purchase_order_template = ICPSudo.get_param('generic_default_email_template_app.purchase_order_template')
        invoice_template = ICPSudo.get_param('generic_default_email_template_app.invoice_template')
        res.update(
            sale_quatation_template=int(sale_quatation_template) or False,
            sale_order_template=int(sale_order_template) or False,
            purchase_quatation_template=int(purchase_quatation_template) or False,
            purchase_order_template=int(purchase_order_template) or False,
            invoice_template=int(invoice_template) or False,
            )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('generic_default_email_template_app.sale_quatation_template', self.sale_quatation_template.id)
        ICPSudo.set_param('generic_default_email_template_app.sale_order_template', self.sale_order_template.id)
        ICPSudo.set_param('generic_default_email_template_app.purchase_quatation_template', self.purchase_quatation_template.id)
        ICPSudo.set_param('generic_default_email_template_app.purchase_order_template', self.purchase_order_template.id)
        ICPSudo.set_param('generic_default_email_template_app.invoice_template', self.invoice_template.id)

class InheritMessase(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.model
    def default_get(self, fields_list):
        attachment_id = self.env.context.get('active_ids')
        company = self.env.user.company_id
        res = super(InheritMessase, self).default_get(fields_list)
        res_config = self.env['res.config.settings'].search([], order="id desc", limit=1)
        if 'model' in res:
            if res['model'] == str('sale.order'):
                active_model = self._context.get('active_model')
                active_id = self._context.get('active_id')
                sale_id = self.env[active_model].browse(active_id)
                if sale_id.state == 'draft':
                    if 'template_id' in res:
                        if company.sale_quatation_template.model_id.model == 'sale.order':
                            res.update({'template_id': company.sale_quatation_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Sale Order !"))
                    else:
                        if company.sale_quatation_template.model_id.model == 'sale.order':
                            res.update({'template_id': company.sale_quatation_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Sale Order !"))
                else:
                    if 'template_id' in res:
                        if company.sale_order_template.model_id.model == 'sale.order':
                            res.update({'template_id': company.sale_order_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Sale Order !"))
                    else:
                        if company.sale_order_template.model_id.model == 'sale.order':
                            res.update({'template_id': company.sale_order_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Sale Order !"))

            elif res['model'] == str('purchase.order'):
                active_model = self._context.get('active_model')
                active_id = self._context.get('active_id')
                purchase_id = self.env[active_model].browse(active_id)
                if purchase_id.state == 'draft':
                    if 'template_id' in res:
                        if company.purchase_quatation_template.model_id.model == 'purchase.order':
                            res.update({'template_id': company.purchase_quatation_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Purchase Order !"))
                    else:
                        if company.purchase_quatation_template.model_id.model == 'purchase.order':
                            res.update({'template_id': company.purchase_quatation_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Purchase Order !"))
                else:
                    if 'template_id' in res:
                        if company.purchase_order_template.model_id.model == 'purchase.order':
                            res.update({'template_id': company.purchase_order_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Purchase Order !"))
                    else:
                        if company.purchase_order_template.model_id.model == 'purchase.order':
                            res.update({'template_id': company.purchase_order_template.id})
                        else:
                            raise UserError(_("You must select email template in general settings only for Purchase Order !"))

            elif res['model'] == str('account.invoice'):
                if 'template_id' in res:
                    if company.invoice_template.model_id.model == 'account.invoice':
                        res.update({'template_id': company.invoice_template.id})
                    else:
                        raise UserError(_("You must select email template in general settings only for Invoice ! "))
                else:
                    if company.invoice_template.model_id.model == 'account.invoice':
                        res.update({'template_id': company.invoice_template.id})
                    else:
                        raise UserError(_("You must select email template in general settings only for Invoice ! "))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: