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
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        action = super(AccountMove, self).action_invoice_sent()
        if self.company_id.id == 17:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            default_template_id = ICPSudo.get_param('givex_invoice_report.ll_mail_template_id')
            if default_template_id  and action.get('context'):
                action['context']['default_template_id'] = int(default_template_id)
            
        return action
