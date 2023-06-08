# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class HrExpense(models.Model):
    _inherit = "hr.expense"

    is_attachment_required = fields.Boolean(string="Attachment required", readonly=False,
                                            related="product_id.is_attachment_required", store=True,
                                            help="Specify whether the product need mandatory attachment.")
    is_from_to_address_required = fields.Boolean(string="From/To required", readonly=False,
                                                 related="product_id.is_from_to_address_required", store=True,
                                                 help="Specify whether the product need mandatory attachment.")
    is_allowance_based_on_vehicle_type = fields.Boolean(string="Vehicle type required", readonly=False,
                                                        related="product_id.is_allowance_based_on_vehicle_type",
                                                        store=True,
                                                        help="Specify "
                                                             "Vehicle"
                                                             " type.")
    vehicle_allowance_type_id = fields.Many2one("hr.vehicle.allowance.type", string="Vehicle Allowance Type",
                                                help="Based on Specify "
                                                     "Vehicle"
                                                     " type.")

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

    amount_tax = fields.Monetary(string='Tax Amount', store=True, readonly=True,
                                 compute='_compute_amount_tax')

    def _get_expense_amount_tax(self):
        """Common function get price tax"""
        amount = self.unit_amount if self.product_has_cost else self.total_amount
        taxes = self.tax_ids.compute_all(
            amount,
            self.currency_id,
            self.quantity,
            self.product_id,
            self.employee_id.user_id.partner_id,
        )
        return sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))

    @api.depends("currency_id", "tax_ids", "total_amount", "unit_amount", "quantity")
    def _compute_amount_tax(self):
        for expense in self:
            amount_tax = expense._get_expense_amount_tax()
            expense.amount_tax = amount_tax

    @api.depends("quantity", "unit_amount", "distance", "tax_ids", "currency_id", "vehicle_allowance_type_id")
    def _compute_amount(self):
        res = super(HrExpense, self)._compute_amount()
        for expense in self:
            if expense.distance >= 0 and expense.vehicle_allowance_type_id:
                distance_amount = (
                        expense.distance
                        * expense.vehicle_allowance_type_id.advisory_fuel_rate
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
        if any(expense.is_attachment_required and expense.attachment_number == 0 for expense in self):
            raise UserError(_("You can not create report without attachment."))
        todo = self.filtered(lambda x: x.payment_mode == 'company_cc')
        if todo:
            if len(todo) == 1:
                expense_name = todo.name
            else:
                dates = todo.mapped('date')
                min_date = format_date(self.env, min(dates))
                max_date = format_date(self.env, max(dates))
                expense_name = min_date if max_date == min_date else "%s - %s" % (min_date, max_date)

            values = {
                'default_company_id': self.company_id.id,
                'default_employee_id': self[0].employee_id.id,
                'default_name': expense_name,
                'default_expense_line_ids': [Command.set(todo.ids)],
                'default_state': 'draft',
                'create': False
            }
            return values
        else:
            return super()._get_default_expense_sheet_values()

    def _get_account_move_line_values(self):
        """Adjust tax amount in accounting move line"""
        move_line_values_by_expense = super()._get_account_move_line_values()
        first_line_ap = False
        for expense in self.filtered(lambda l: l.sheet_id.tax_adjust and l.tax_ids):
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = (
                    expense.sheet_id.accounting_date
                    or expense.date
                    or fields.Date.context_today(expense)
            )

            # Find price diff origin and adjust
            total_amount_tax = expense.sheet_id._get_expense_total_amount_tax()
            diff_price_tax_currency = total_amount_tax - expense.sheet_id.total_amount_tax
            diff_price_tax = expense.sheet_id._get_expense_balance(
                diff_price_tax_currency, account_date
            )
            if first_line_ap:
                continue
            first_line_tax = False
            # NOTE: Core odoo value `move_line_values_by_expense` sort by
            # taxes move lines and destination move line in order.
            for move_line_values in move_line_values_by_expense[expense.id]:
                # Tax adjust move line. if multi tax, we compute with first line tax/destination only
                if "tax_base_amount" in move_line_values:
                    if first_line_tax:
                        continue
                    new_tax_amount = move_line_values["debit"] - diff_price_tax
                    move_line_values.update(
                        {
                            "debit": new_tax_amount if new_tax_amount > 0 else 0,
                            # move to credit, if adjust tax more than tax calculate
                            "credit": abs(new_tax_amount) if new_tax_amount < 0 else 0,
                            "amount_currency": move_line_values["amount_currency"]
                                               - diff_price_tax_currency,
                        }
                    )
                    first_line_tax = True
                    continue
                # Source move line, For case include price
                if (
                        expense.tax_ids.filtered("price_include")
                        and move_line_values.get("account_id") == account_src.id
                ):
                    move_line_values.update(
                        {
                            "debit": move_line_values["debit"] + diff_price_tax
                            if move_line_values["debit"] > 0
                            else 0,
                            "credit": move_line_values["credit"] + diff_price_tax
                            if move_line_values["credit"] > 0
                            else 0,
                            "amount_currency": move_line_values["amount_currency"]
                                               + diff_price_tax_currency,
                        }
                    )
                    first_line_ap = True
                    continue
                # Destination adjust move line, For case exclude price
                elif (
                        not expense.tax_ids.filtered("price_include")
                        and move_line_values.get("account_id") == account_dst
                ):
                    move_line_values.update(
                        {
                            "debit": move_line_values["debit"] - diff_price_tax
                            if move_line_values["debit"] > 0
                            else 0,
                            "credit": move_line_values["credit"] - diff_price_tax
                            if move_line_values["credit"] > 0
                            else 0,
                            "amount_currency": move_line_values["amount_currency"]
                                               - diff_price_tax_currency,
                        }
                    )
                    first_line_ap = True
                    continue

        return move_line_values_by_expense


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    total_amount_tax = fields.Monetary(string='Tax', store=True, readonly=True,
                                       compute='_compute_total_amount_tax')
    tax_adjust = fields.Boolean(
        help="trigger line with adjust tax"
    )

    def _get_expense_balance(self, amount, account_date):
        return self.currency_id._convert(
            amount, self.company_id.currency_id, self.company_id, account_date
        )

    def _get_expense_total_amount_tax(self):
        """Common function get price tax"""
        total_amount_tax = 0.0
        for expense in self.expense_line_ids:
            amount = expense.unit_amount if expense.product_has_cost else expense.total_amount
            taxes = expense.tax_ids.compute_all(
                amount,
                expense.currency_id,
                expense.quantity,
                expense.product_id,
                expense.employee_id.user_id.partner_id,
            )

            total_amount_tax += sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
        return total_amount_tax

    @api.onchange("total_amount_tax")
    def _onchange_amount_tax(self):
        for sheet in self:
            if sheet.total_amount_tax != sheet._get_expense_total_amount_tax():
                sheet.tax_adjust = True
            else:
                sheet.tax_adjust = False

    @api.depends("expense_line_ids.amount_tax")
    def _compute_total_amount_tax(self):
        total_tax = 0.0
        for sheet in self:
            if sheet.tax_adjust:
                continue
            for expense_line in sheet.expense_line_ids:
                total_tax += expense_line.amount_tax
            sheet.total_amount_tax = total_tax
