# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class VehicleAllowanceType(models.Model):
    _name = "hr.vehicle.allowance.type"
    _description = "Vehicle Allowance Type"

    name = fields.Char()
    active = fields.Boolean(default=True, help="Set active to false to hide the Vehicle Allowance Type without "
                                               "removing it.")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this vehicle allowance type")
    sequence = fields.Integer(help='Used to order Journals in the dashboard view', default=10)
    mean_mpg = fields.Float("Mean MPG", digits=(16, 2))
    fuel_rate_per_ltr = fields.Float("Fuel Price (Per Litre)", digits=(16, 2))
    fuel_rate_per_gal = fields.Float("Fuel Price (Per Gallon)", digits=(16, 2))
    rate_per_mile = fields.Float("Fuel Price (Per Gallon)", digits=(16, 2))
    advisory_fuel_rate = fields.Float("Advisory Rate", digits=(16, 2))
