# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    requires_ff_approval = fields.Boolean('Requires Fulfillment Approval', help="Does this product when added to a sale order requires approval from Fulfillment?")
    exclude_from_price_approval = fields.Boolean('Exclude from Quotation Price Approval', default=False, copy=False, help="Exclude this product from requiring sale order (quotation) approval when the price is changed?")

