# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo import api, fields, models, _


class HrExpense(models.Model):
    _inherit = "hr.expense"
    _description = "Expense"

    is_attachment_required = fields.Boolean(string="Attachment Required", readonly=False,
                                            related="product_id.is_attachment_required", store=True,
                                            help="Specify whether the product need mandatory attachment.")
    is_from_to_address_required = fields.Boolean(string="From/To Required", readonly=False,
                                            related="product_id.is_from_to_address_required", store=True,
                                            help="Specify whether the product need mandatory attachment.")

    # from address fields
    from_street = fields.Char()
    from_street2 = fields.Char()
    from_zip = fields.Char(change_default=True)
    from_city = fields.Char()
    from_state_id = fields.Many2one("res.country.state", string=' From State', ondelete='restrict',
                               domain="[('country_id', '=?', from_country_id)]")
    from_country_id = fields.Many2one('res.country', string='From Country', ondelete='restrict')
    from_country_code = fields.Char(related='from_country_id.code', string="From Country Code")
    from_latitude = fields.Float(string='From Geo Latitude', digits=(10, 7))
    from_longitude = fields.Float(string='From Geo Longitude', digits=(10, 7))

    # to address fields
    to_street = fields.Char()
    to_street2 = fields.Char()
    to_zip = fields.Char(change_default=True)
    to_city = fields.Char()
    to_state_id = fields.Many2one("res.country.state", string='To State', ondelete='restrict',
                                  domain="[('country_id', '=?', to_country_id)]")
    to_country_id = fields.Many2one('res.country', string='To Country', ondelete='restrict')
    to_country_code = fields.Char(related='to_country_id.code', string="To Country Code")
    to_latitude = fields.Float(string='To Geo Latitude', digits=(10, 7))
    to_longitude = fields.Float(string='To Geo Longitude', digits=(10, 7))
    distance = fields.Float(string="Distance (KM)")
    payment_mode = fields.Selection(selection_add=[('company_cc', 'Company Credit Card')])

    @api.depends("quantity", "unit_amount", "distance", "tax_ids", "currency_id")
    def _compute_amount(self):
        res = super(HrExpense, self)._compute_amount()
        for expense in self:
            if expense.distance >= 0:
                distance_amount = (
                    expense.distance
                    * expense.company_id.per_distance_reimbursement_rate
                )
                total = expense.unit_amount + distance_amount
                taxes = expense.tax_ids.compute_all(
                    total,
                    expense.currency_id,
                    expense.quantity,
                    expense.product_id,
                    expense.employee_id.user_id.partner_id,
                )
                expense.total_amount = taxes.get("total_included")
        return res

    def _get_default_expense_sheet_values(self):
        if any(expense.is_attachment_required and expense.attachment_number ==0 for expense in self):
            raise UserError(_("You can not create report without attachment."))
        return super()._get_default_expense_sheet_values()
