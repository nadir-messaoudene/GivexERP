# $Id: partner.py,v 1.1 2020/08/20 18:33:29 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.

import time
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    x_studio_entity_id = fields.Char(string='Billing Entity ID',size=16, help="Gives the operational mapping id between Odoo and Givex Admin ID.",
                                     translate=True)
    x_studio_entity_type = fields.Selection(selection=[('client', 'Client'), ('merchant', 'Merchant'), ('franchise', 'Franchise'), ('store', 'Store'),
                                                       ('partner', 'Partner'), ('dealer', 'Dealer')], string='Billing Entity Type',
                                            help="This will define the type of Business Entity.")
    x_studio_frequency = fields.Selection(selection=[('monthly', 'Monthly'),('quarterly', 'Quarterly'),('yearly', 'Yearly')], string='Frequency Of Billing',
                                          help="This defines the frequency of billing for transaction billing .", default='monthly')
    x_studio_threshold = fields.Float("Amount Threshold", help="Amount Threshold for Increment transaction")

    @api.onchange('x_studio_entity_id')
    def _onchange_x_studio_entity_id(self):
        if not self.x_studio_entity_id.isdigit():
            raise ValidationError(_('UserError','Please Enter Numeric value for Billing Entity ID'))
        return {}
