# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    threshold_value = fields.Float('Threshold Value')
    apply_threshold_website_portal = fields.Boolean('Apply for website, portal')
    
class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    # Check Threshold when submit payment from Backend
    def action_create_payments(self):
        PayAcq = self.env['payment.acquirer']
        if self.journal_id.id:
            payacq_ids = PayAcq.sudo().search([('company_id', 'in', self.env.user.company_ids.ids)])
            for acquirer in payacq_ids:
                if acquirer.journal_id == self.journal_id:
                    if acquirer.threshold_value and acquirer.threshold_value < self.amount:
                        raise ValidationError("Can not process a payment over the threshold.")
                    break
        
        return super(AccountPaymentRegister, self).action_create_payments()