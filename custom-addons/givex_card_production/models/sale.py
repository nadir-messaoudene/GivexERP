# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.tools import float_compare

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_proofing_id = fields.Many2one('res.partner', string='Card Proofing Address',
                                          readonly=True, required=False,
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'sale': [('readonly', False)],
                                                  'new': [('readonly', False)],
                                                  'pending_approval': [('readonly', False)],
                                                  'pending_ff_approval': [('readonly', False)]},
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          context="{'parent_id': partner_id}", )

    has_card_product = fields.Boolean(compute='_check_card_production_in_order_line',
                                      string='Has Card Production', readonly=True, default=False)
    proofing_address_incomplete = fields.Char(string='Is Proofing address Complete',
                                              compute='_is_proofing_address_complete', readonly=True)
    partner_name = fields.Char(string='Partner name', readonly=True)

    @api.depends('order_line.product_id')
    def _check_card_production_in_order_line(self):
        for order in self:
            order.has_card_product = False
            proofing = False
            
            for line in order.order_line:
                if line.product_template_id.categ_id.name == 'Cards & Card Proofs':
                    order.has_card_product = True
                    
                    # Set the card proofing address
                    if not order.partner_proofing_id:
                        addr = self.partner_id.address_get(['proofing'], return_default=False)
                        if addr.get('proofing'):
                            order.update({
                                'partner_proofing_id': addr['proofing'],
                            })
                    proofing = True
            
            # If no card proofing product found, then
            # clear the proofing address
            if not proofing:
                order.update({
                    'partner_proofing_id': False,
                })

    @api.onchange('partner_id')
    def set_partner_proofing_id(self):
        address = False
        partner_name = False
        if self.partner_id:
            partner_name = self.partner_id.name
        if self.has_card_product:
            # Set the card proofing address
            addr = self.partner_id.address_get(['proofing'], return_default=False)
            if addr.get('proofing'):
                address = addr['proofing']
        
        self.update({
            'partner_proofing_id': address,
            'partner_name': partner_name,
        })

        return

    @api.depends('partner_proofing_id')
    def _is_proofing_address_complete(self):
        for record in self:
            record['proofing_address_incomplete'] = False
            if record.partner_proofing_id:
                missing_str = []
                if not record.partner_proofing_id.street:
                    missing_str.append('Street') 
                if not record.partner_proofing_id.city:
                    missing_str.append('City')
                if not record.partner_proofing_id.state_id:
                    missing_str.append('State')
                if not record.partner_proofing_id.phone:
                    missing_str.append('Phone')
                if not record.partner_proofing_id.email:
                    missing_str.append('Email')
                
                if missing_str:
                    record['proofing_address_incomplete'] = 'Card Proofing Address is incomplete - missing {0} !'.format(', '.join(missing_str))
