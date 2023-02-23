# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
import textwrap


from odoo import api, fields, models

_logger = logging.getLogger(__name__)

SEPARATOR = "\r\n"

class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"
    _description = "Batch Payment"

    td_eft_file = fields.Binary(string="TD EFT file")
    td_eft_filename = fields.Char(string="Filename")
    td_eft_file_creation_sequence = fields.Char(string="TD EFT file creation sequence")

    @api.model
    def _get_td_file_creation_seq(self, batch_type, sequence_date):
        if batch_type == "outbound":
            sequence_code = "td.outbound.batch.payment"
            return (
                self.env["ir.sequence"]
                .with_context(sequence_date=sequence_date)
                .next_by_code(sequence_code)
            )
        return " " * 4

    def _wraptext_lines(self, contents):
        wrapped_text = textwrap.fill(contents, width=80)
        lines = wrapped_text.split('\n')
        filled_lines = [line.ljust(80) for line in lines]
        filled_text = '\n'.join(filled_lines)
        return filled_text

    def _eft_td_header(self):
        header_line = " " * 80
        header_positions = [0, 1, 11, 12, 15, 21, 36, 45, 57, 61]
        if self.journal_id and self.date:
            bound_type = self.batch_type == "outbound" and "C" or ""
            batch_type = self.batch_type
            journal_id = self.journal_id
            td_originator_code = (
                journal_id.td_originator_code
                and str(journal_id.td_originator_code).strip()
                or "0" * 10
            )
            td_cpa_code = journal_id.td_cpa_code and str(journal_id.td_cpa_code).strip()
            td_originator_short_name = (
                journal_id.td_originator_short_name
                and str(journal_id.td_originator_short_name).strip()
            )
            td_institution_id_return = (
                journal_id.td_institution_id_return
                and str(journal_id.td_institution_id_return).strip()
                or "0" * 9
            )
            td_account_no_return = (
                journal_id.td_account_no_return
                and str(journal_id.td_account_no_return).strip()
                or " " * 12
            )
            if batch_type:
                if not self.td_eft_file_creation_sequence:
                    td_file_creation_seq = str(
                        self._get_td_file_creation_seq(
                            batch_type, fields.Date.context_today(self)
                        )
                    ).strip()
                    self.td_eft_file_creation_sequence = td_file_creation_seq
                else:
                    td_file_creation_seq = self.td_eft_file_creation_sequence
            date = str(self.date.strftime("%d%m%y")).strip()
            header_data = [
                "H",
                td_originator_code,
                bound_type,
                td_cpa_code,
                date,
                td_originator_short_name,
                td_institution_id_return,
                td_account_no_return,
                td_file_creation_seq,
            ]
            for p, d in zip(header_positions, header_data):
                header_line = header_line[:p] + d + header_line[p + 1 :]
            return header_line
        else:
            return False

    def _eft_td_transation_line(self, payment=None):
        transaction_line = " " * 80
        transaction_positions = [0, 1, 24, 30, 49, 58, 70]

        if payment and payment.partner_bank_account_id:
            pay_name = (
                payment.partner_id
                and str(payment.partner_id.name[:23]).strip()
                or " " * 23
            )
            due_date = (
                payment.payment_date
                and str(payment.payment_date.strftime("%d%m%y")).strip()
                or " " * 6
            )
            originator_reference = (
                payment.communication and str(payment.communication).strip() or " " * 19
            )
            institution_transit_number = (
                payment.partner_bank_account_id.aba_routing
                and str("0" + payment.partner_bank_account_id.aba_routing).strip()
                or "0" + " " * 8
            )
            account_number = (
                payment.partner_bank_account_id.acc_number
                and str(payment.partner_bank_account_id.acc_number).strip() + " " * 5
                or " " * 12
            )
            amount = "0" * 10
            if payment.amount > 0:
                amount = round(payment.amount * 100)
                prefix_zero_count = 10 - len(str(amount))
                if prefix_zero_count > 0:
                    amount = str("0" * prefix_zero_count + str(amount))
                else:
                    amount = str(amount)
            transaction_data = [
                "D",
                pay_name,
                due_date,
                originator_reference,
                institution_transit_number,
                account_number,
                amount,
            ]
            for p, d in zip(transaction_positions, transaction_data):
                transaction_line = transaction_line[:p] + d + transaction_line[p + 1 :]
            return transaction_line

    def _eft_td_footer(self):
        footer_line = " " * 80
        footer_positions = [0, 1, 9]
        if self.payment_ids:
            if len(self.payment_ids) > 0:
                prefix_transaction_zero_count = 8 - len(str(len(self.payment_ids)))
                if prefix_transaction_zero_count > 0:
                    td_transaction_count = str(
                        "0" * prefix_transaction_zero_count + str(len(self.payment_ids))
                    ).strip()
                else:
                    td_transaction_count = str(len(self.payment_ids)).strip()
            else:
                td_transaction_count = "0" * 8
            total_amount = sum(payment_id.amount for payment_id in self.payment_ids)
            if total_amount > 0:
                total_amount = round(total_amount * 100)
                prefix_amount_zero_count = 14 - len(str(total_amount))
                if prefix_amount_zero_count > 0:
                    total_amount = str(
                        "0" * prefix_amount_zero_count + str(total_amount)
                    )
                else:
                    total_amount = str(total_amount).strip()
            else:
                total_amount = "0" * 14
            footer_data = ["T", td_transaction_count, total_amount]
            for p, d in zip(footer_positions, footer_data):
                footer_line = footer_line[:p] + d + footer_line[p + 1 :]
            return footer_line
        else:
            return False

    def generate_td_eft(self):
        for batch_payment in self:
            if not batch_payment.td_eft_file:
                header_line = batch_payment._eft_td_header()
                footer_line = batch_payment._eft_td_footer()
                if header_line and footer_line:
                    data = header_line + "\n"
                    for payment in batch_payment.payment_ids:
                        if payment:
                            data_line = batch_payment._eft_td_transation_line(
                                payment=payment
                            )
                            _logger.info("data_line : {}".format(data_line))
                            if data_line:
                                data += str(data_line) + "\n"
                    data += footer_line

                    data = self._wraptext_lines(data)

                    batch_payment.td_eft_file = base64.b64encode(data.encode())
                file_name = (
                    "EFT TDB"
                    + (
                        batch_payment.currency_id
                        and str(batch_payment.currency_id.name)
                        or ""
                    )
                    + " "
                    + str(batch_payment.date.strftime("%Y%m%d"))
                    + "-"
                    + str(batch_payment.td_eft_file_creation_sequence)
                    + ".txt"
                )
                batch_payment.td_eft_filename = file_name
            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/account.batch.payment/%s/td_eft_file/%s?download=true"
                % (batch_payment.id, batch_payment.td_eft_filename),
            }
