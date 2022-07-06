# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ll_mail_template_id = fields.Many2one(
        string='Loyalty Lane Mail Template',
        comodel_name='mail.template',
        ondelete='set null',
        domain=[('model', '=', 'account.move')],
    )


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ll_mail_template_id = ICPSudo.get_param('givex_invoice_report.ll_mail_template_id')
        if ll_mail_template_id:
            res.update(ll_mail_template_id=int(ll_mail_template_id))
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('givex_invoice_report.ll_mail_template_id', self.ll_mail_template_id.id)
