# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError



class AccountMove(models.Model):
    _inherit = 'account.move'


    def action_invoice_sent(self):
        action = super(AccountMove, self).action_invoice_sent()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        if self.company_id.id == 17:
            default_template_id = ICPSudo.get_param('givex_invoice_report.ll_mail_template_id')
            if default_template_id  and action.get('context'):
                action['context']['default_template_id'] = int(default_template_id)
        elif not self.company_id.id == 30:
            default_template_id = ICPSudo.get_param('givex_invoice_report.csh_mail_template_id')
            if default_template_id and action.get('context'):
                action['context']['default_template_id'] = int(default_template_id)
            
        return action
