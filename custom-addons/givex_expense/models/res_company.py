# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    use_per_distance_rate = fields.Boolean()
    per_distance_reimbursement_rate = fields.Float(
        string="Per Distance (KM) reimbursement rate"
    )
