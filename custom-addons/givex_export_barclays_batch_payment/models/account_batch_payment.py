# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models

SEPARATOR = "\r\n"


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"
    _description = "Batch Payment"

    def export_barclays_batch_to_csv(self):
        report_action = {
            "type": "ir.actions.report",
            "report_name": "report_csv.batch_payment_csv",
            "report_type": "csv",
            "report_file": "report_csv.batch_payment_csv",
            "print_report_name": "(object._get_report_base_filename())",
            "model": "account.batch.payment",
            "attachment_use": False,
            "name": "Export to CSV",
        }
        if self.payment_method_id.code == "bacs":
            return report_action
        return True

    def export_barclays_batch_to_xlsx(self):
        report_action = {
            "type": "ir.actions.report",
            "report_name": "report_xlsx.batch_payment_xlsx",
            "report_type": "xlsx",
            "report_file": "report_xlsx.batch_payment_xlsx",
            "print_report_name": "(object._get_report_base_filename())",
            "model": "account.batch.payment",
            "attachment_use": False,
            "name": "Export to XLS",
        }
        if self.payment_method_id.code == "bacs":
            return report_action
        return True

    def _get_report_base_filename(self):
        self.ensure_one()
        return "%s - (%s)" % (self.sudo().name, self.sudo().batch_type)
