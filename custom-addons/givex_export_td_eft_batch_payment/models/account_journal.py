# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    payment_method_code = fields.Char(
        string="Payment Code", compute="_compute_td_payment_code"
    )
    has_td_EFT_payment_method = fields.Boolean(
        compute="_compute_has_td_EFT_payment_method"
    )
    td_originator_code = fields.Char(
        string="TD Bank Originator ID",
        size=10,
        help="Provided by TD Bank (must be uppercase) Format: AN.",
    )
    td_cpa_code = fields.Char(
        string="TD CPA Code",
        size=3,
        help="Canadian Payment Association transaction code. Format: AN.",
    )
    td_originator_short_name = fields.Char(
        string="Originator Short Name",
        size=15,
        help="Company name, shortened into a field length of 15 characters. Format: AN. If you are a Service Bureau or a Processing Agent, the name of the transaction’s originator. Format: AN",
    )
    td_institution_id_return = fields.Char(
        string="Institution ID/Transit Number for Returned Transactions",
        size=9,
        help="Must be “0004” for TD followed by your 5 digit branch transit number. eg: Example: 000410202. Format: N",
    )
    td_account_no_return = fields.Char(
        string="Account Number for Returned Transactions",
        size=12,
        help="Must be a TD Commercial account number where dishonored transactions will be returned. 11 digits followed by 1 space. Format : AN",
    )

    @api.depends("outbound_payment_method_line_ids.payment_method_id.code")
    def _compute_td_payment_code(self):
        for rec in self:
            rec.payment_method_code = (
                any(
                    payment_method.payment_method_id.code == "td"
                    for payment_method in rec.outbound_payment_method_line_ids
                )
                and "td"
                or ""
            )

    @api.depends("outbound_payment_method_line_ids.payment_method_id.code")
    def _compute_has_td_EFT_payment_method(self):
        for rec in self:
            rec.has_td_EFT_payment_method = any(
                payment_method.payment_method_id.code == "td"
                for payment_method in rec.outbound_payment_method_line_ids
            )

    def _default_outbound_payment_methods(self):
        res = super()._default_outbound_payment_methods()
        if self._is_payment_method_available("td"):
            res |= self.env.ref(
                "givex_export_td_eft_batch_payment.account_payment_method_td"
            )
        return res

    @api.model
    def _create_td_batch_payment_outbound_sequence(self):
        IrSequence = self.env["ir.sequence"]
        if IrSequence.search([("code", "=", "td.outbound.batch.payment")]):
            return
        return IrSequence.sudo().create(
            {
                "name": _("TD Outbound Batch Payments Sequence"),
                "padding": 4,
                "code": "td.outbound.batch.payment",
                "number_next": 1,
                "number_increment": 1,
                "use_date_range": False,
                "prefix": "",
                # by default, share the sequence for all companies
                "company_id": False,
            }
        )
