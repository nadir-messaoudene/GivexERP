# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import csv
import io

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"
    _description = "Batch Payment"

    payment_method_code = fields.Char(
        related="payment_method_id.code", string="Payment method code", store=True
    )
    barclay_csv_file = fields.Binary(string="Barclays CSV file")
    barclay_csv_filename = fields.Char(string="Barclays Filename")

    def export_barclays_batch_to_csv(self):
        if self.payment_method_id.code == "bacs":
            self.barclay_csv_file = self.generate_csv_barclays_data()
            self.barclay_csv_filename = self._get_report_base_filename() + ".csv"
        return True

    def generate_csv_barclays_data(self):

        # Define delimiter and header row
        delimiter = ","
        # header = [
        #     "Destination Sort Code",
        #     "Destination Account Number",
        #     "Destination Account Type",
        #     "Bacs Code",
        #     "Debit Sort Code",
        #     "Debit Account Number",
        #     "Free Format",
        #     "Amount",
        #     "Originator Name",
        #     "Payment Reference",
        #     "Destination Account Name",
        #     "Processing Date",
        # ]

        # Define data rows
        data = []
        for batch_payment in self:
            if (
                batch_payment.payment_method_id
                and batch_payment.payment_method_id.code == "bacs"
            ):
                for payment in batch_payment.payment_ids:
                    if payment.partner_id:
                        destination_account_name = payment.partner_id.name
                    elif payment.partner_bank_id.acc_holder_name:
                        destination_account_name = (
                            payment.partner_bank_id.acc_holder_name
                        )
                    elif payment.partner_bank_id.partner_id:
                        destination_account_name = (
                            payment.partner_bank_id.partner_id.name
                        )
                    else:
                        destination_account_name = ""
                    if payment.amount:
                        amount = round(payment.amount * 100)
                        amount = str(amount)[:11]
                        amount = int(amount)
                    if not payment.journal_id.bank_account_id:
                        raise ValidationError(
                            _("Company bank account is missing in bank journal.")
                        )

                    data.append(
                        [
                            payment.partner_bank_id.aba_routing
                            and str(payment.partner_bank_id.aba_routing[:6])
                            or "",
                            payment.partner_bank_id.acc_number
                            and str(payment.partner_bank_id.acc_number[:8])
                            or "",
                            payment.partner_bank_id.barclays_account_type
                            and payment.partner_bank_id.barclays_account_type
                            or "",
                            payment.partner_bank_id.bacs_code
                            and str(payment.partner_bank_id.bacs_code[:2])
                            or "",
                            payment.journal_id.bank_account_id.aba_routing
                            and str(payment.journal_id.bank_account_id.aba_routing[:6])
                            or "",
                            payment.journal_id.bank_account_id.acc_number
                            and str(payment.journal_id.bank_account_id.acc_number[:8])
                            or "",
                            "",
                            amount or "0.00",
                            payment.journal_id.bank_account_id.acc_holder_name
                            and payment.journal_id.bank_account_id.acc_holder_name[:18]
                            or "",
                            payment.ref and payment.ref[:18] or "",
                            destination_account_name
                            and destination_account_name[:18]
                            or "",
                            payment.date or "",
                        ]
                    )

        # Build CSV data
        csv_data = []
        # no header
        # csv_data.append(header)
        for row in data:
            csv_data.append(row)

        # Convert CSV data to string
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, delimiter=delimiter)
        for row in csv_data:
            writer.writerow(row)
        csv_string = csv_file.getvalue()

        # Return CSV data as string
        csv_binary = base64.b64encode(csv_string.encode())
        return csv_binary

    def _get_report_base_filename(self):
        self.ensure_one()
        if self.payment_method_id.code == "bacs":
            return "%s - (%s) - Barclays" % (self.sudo().name, self.sudo().batch_type)

    def re_generate_barclays_batch_to_csv(self):
        for batch_payment in self:
            if batch_payment.barclay_csv_file:
                batch_payment.export_barclays_batch_to_csv()