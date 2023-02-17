import csv

from odoo import models, _
from odoo.exceptions import UserError, ValidationError


class BatchPaymentBarclaysCSV(models.AbstractModel):
    _name = "report.report_csv.batch_payment_barclays_csv"
    _description = "csv report"
    _inherit = "report.report_csv.abstract"

    def generate_csv_report(self, writer, data, batch_payments):
        for batch_payment in batch_payments.sudo():
            if batch_payment.payment_method_id and batch_payment.payment_method_id.code == "bacs":
                for payment in batch_payment.payment_ids:
                    if payment.partner_id:
                        destination_account_name = payment.partner_id.name
                    elif payment.partner_bank_account_id.acc_holder_name:
                        destination_account_name = (
                            payment.partner_bank_account_id.acc_holder_name
                        )
                    elif payment.partner_bank_account_id.partner_id:
                        destination_account_name = (
                            payment.partner_bank_account_id.partner_id.name
                        )
                    else:
                        destination_account_name = ""
                    if payment.amount:
                        amount = round(payment.amount * 100)
                        amount = str(amount)[:11]
                        amount = int(amount)
                    if not payment.journal_id.bank_account_id:
                        raise ValidationError(
                            _('Company bank account is missing in bank journal.'))

                    writer.writerow(
                        {
                            "Destination Sort Code": payment.partner_bank_account_id.aba_routing
                            and str(payment.partner_bank_account_id.aba_routing[:6])
                            or "",
                            "Destination Account Number": payment.partner_bank_account_id.acc_number
                            and str(payment.partner_bank_account_id.acc_number[:8])
                            or "",
                            "Destination Account Type": payment.partner_bank_account_id.barclays_account_type
                            and payment.partner_bank_account_id.barclays_account_type
                            or "",
                            "Bacs Code": payment.partner_bank_account_id.bacs_code
                            and int(payment.partner_bank_account_id.bacs_code[:2])
                            or "",
                            "Debit Sort Code": payment.journal_id.bank_account_id.aba_routing
                            and int(payment.journal_id.bank_account_id.aba_routing[:6])
                            or "",
                            "Debit Account Number": payment.journal_id.bank_account_id.acc_number
                            and int(payment.journal_id.bank_account_id.acc_number[:8])
                            or "",
                            "Free Format": "",
                            "Amount": amount or "0.00",
                            "Originator Name": payment.journal_id.bank_account_id.acc_holder_name
                            and payment.journal_id.bank_account_id.acc_holder_name[:18]
                            or "",
                            "Payment Reference": payment.communication and payment.communication[:18] or "",
                            "Destination Account Name": destination_account_name
                            and destination_account_name[:18]
                            or "",
                            "Processing Date": payment.payment_date or "",
                        }
                    )

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("Destination Sort Code")
        res["fieldnames"].append("Destination Account Number")
        res["fieldnames"].append("Destination Account Type")
        res["fieldnames"].append("Bacs Code")
        res["fieldnames"].append("Debit Sort Code")
        res["fieldnames"].append("Debit Account Number")
        res["fieldnames"].append("Free Format")
        res["fieldnames"].append("Amount")
        res["fieldnames"].append("Originator Name")
        res["fieldnames"].append("Payment Reference")
        res["fieldnames"].append("Destination Account Name")
        res["fieldnames"].append("Processing Date")
        res["delimiter"] = ","
        res["quoting"] = csv.QUOTE_NONE
        return res


class BatchPaymentBarclaysXLSX(models.AbstractModel):
    _name = "report.report_xlsx.batch_payment_barclays_xlsx"
    _description = "xlsx report"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, batch_payments):
        # Removed header
        # writer.writeheader()

        for batch_payment in batch_payments.sudo():
            if batch_payment.payment_method_id and batch_payment.payment_method_id.code == "bacs":
                report_name = batch_payment.name
                sheet = workbook.add_worksheet(report_name[:31])
                locked = workbook.add_format({"locked": True})
                numbersformat_locked = workbook.add_format(
                    {"locked": True, "num_format": "0"}
                )
                date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
                sheet.protect("givex@123")
                payment_row = 0
                payment_col = 0
                for payment in batch_payment.payment_ids:
                    if payment.partner_id:
                        destination_account_name = payment.partner_id.name
                    elif payment.partner_bank_account_id.acc_holder_name:
                        destination_account_name = (
                            payment.partner_bank_account_id.acc_holder_name
                        )
                    elif payment.partner_bank_account_id.partner_id:
                        destination_account_name = (
                            payment.partner_bank_account_id.partner_id.name
                        )
                    else:
                        destination_account_name = ""
                    if payment.amount:
                        amount = round(payment.amount * 100)
                        amount = str(amount)[:11]
                        amount = int(amount)
                    if not payment.journal_id.bank_account_id:
                        raise ValidationError(
                            _('Company bank account is missing in bank journal.'))
                    sheet.write(
                        payment_row,
                        payment_col + 0,
                        payment.partner_bank_account_id.aba_routing
                        and int(payment.partner_bank_account_id.aba_routing[:6])
                        or "",
                        numbersformat_locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 1,
                        payment.partner_bank_account_id.acc_number
                        and int(payment.partner_bank_account_id.acc_number[:8])
                        or "",
                        numbersformat_locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 2,
                        payment.partner_bank_account_id.barclays_account_type
                        and payment.partner_bank_account_id.barclays_account_type
                        or "",
                        locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 3,
                        payment.partner_bank_account_id.bacs_code
                        and int(payment.partner_bank_account_id.bacs_code[:2])
                        or "",
                        numbersformat_locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 4,
                        payment.journal_id.bank_account_id.aba_routing
                        and int(payment.journal_id.bank_account_id.aba_routing[:6])
                        or "",
                        numbersformat_locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 5,
                        payment.journal_id.bank_account_id.acc_number
                        and int(payment.journal_id.bank_account_id.acc_number[:8])
                        or "",
                        numbersformat_locked,
                    )
                    sheet.write(payment_row, payment_col + 6, "", locked)
                    sheet.write(
                        payment_row, payment_col + 7, amount or "0", numbersformat_locked
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 8,
                        payment.journal_id.bank_account_id.acc_holder_name
                        and payment.journal_id.bank_account_id.acc_holder_name[:18]
                        or "",
                        locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 9,
                        payment.communication and payment.communication[:18] or "",
                        locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 10,
                        destination_account_name and destination_account_name[:18] or "",
                        locked,
                    )
                    sheet.write(
                        payment_row,
                        payment_col + 11,
                        payment.payment_date or "",
                        date_format,
                    )
                    payment_row = payment_row + 1
