# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    requires_ff_approval = fields.Boolean('Requires Fulfillment Approval', help="Does this product when added to a sale order requires approval from Fulfillment?")
