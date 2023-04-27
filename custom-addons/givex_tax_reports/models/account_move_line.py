# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models

SEPARATOR = "\r\n"


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def export_journal_items_to_xlsx(self):
        report_action = {
            "type": "ir.actions.report",
            "report_name": "report_xlsx.account_move_line_xlsx",
            "report_type": "xlsx",
            "report_file": "report_xlsx.move_line_xlsx",
            "print_report_name": "(object._get_report_base_filename())",
            "model": "account.move.line",
            "attachment_use": False,
            "name": "Export to XLS",
        }
        return report_action
