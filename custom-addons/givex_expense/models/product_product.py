# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    is_attachment_required = fields.Boolean(string="Attachment required", readonly=False, help="Specify whether the "
                                                                                               "product need "
                                                                                               "mandatory attachment.")
    is_from_to_address_required = fields.Boolean(string="From/To address required", readonly=False,
                                            help="Specify whether the product need from/to address.")
    is_allowance_based_on_vehicle_type = fields.Boolean(string="Vehicle type required", readonly=False, help="Specify "
                                                                                                             "Vehicle"
                                                                                                             " type.")
