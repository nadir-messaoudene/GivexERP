from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_per_distance_rate = fields.Boolean(
        string="Use per distance(KM) reimbursement rate",
        related="company_id.use_per_distance_rate",
        readonly=False,
    )
    per_distance_reimbursement_rate = fields.Float(
        string="Reimbursement per distance(KM) rate",
        related="company_id.per_distance_reimbursement_rate",
        readonly=False,
    )
