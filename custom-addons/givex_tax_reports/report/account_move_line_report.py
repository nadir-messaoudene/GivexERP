from odoo import models, _
from odoo.exceptions import MissingError

MOVE_TYPES = {
    'entry': 'Journal Entry',
    'out_invoice': 'Customer Invoice',
    'out_refund': 'Customer Credit Note',
    'in_invoice': 'Vendor Bill',
    'in_refund': 'Vendor Credit Note',
    'out_receipt': 'Sales Receipt',
    'in_receipt': 'Purchase Receipt',
}


class MoveLineUnexpectedTaxXLSX(models.AbstractModel):
    _name = "report.report_xlsx.move_line_unexpected_tax_xlsx"
    _description = "xlsx report"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, move_lines):
        # Create a new worksheet
        sheet = workbook.add_worksheet('Unexpected Tax Report')
        move_line_row = 0
        move_line_col = 0
        count = 0
        # Write the header row to the worksheet
        # Add the header row to the worksheet
        bold = workbook.add_format({'bold': True})
        sheet.write('A1', 'No', bold)
        sheet.write('B1', 'Type', bold)
        sheet.write('C1', 'Account', bold)
        sheet.write('D1', 'Nominal', bold)
        sheet.write('E1', 'Date', bold)
        sheet.write('F1', 'Ref', bold)
        sheet.write('G1', 'Net Amount', bold)
        sheet.write('H1', 'Tax', bold)
        sheet.write('I1', 'Estimated Tax', bold)
        sheet.write('J1', 'Tax Code', bold)
        move_line_row += 1
        unique_month_year = set()
        for move_line in move_lines.sudo():
            if move_line.tax_line_id:
                if move_line.tax_base_amount and move_line.amount_currency:
                    tax_from_base_amount = (move_line.tax_base_amount * (move_line.tax_line_id.amount / 100))
                    tax_from_base_amount = move_line.currency_id.round(tax_from_base_amount)
                    if move_line.currency_id.compare_amounts(tax_from_base_amount, abs(move_line.amount_currency)) != 0:
                        unique_month_year.add((move_line.date.strftime('%B'), move_line.date.year))
                        report_name = "Unexpected Tax Report for " + str(unique_month_year)
                        date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
                        sheet.write(
                            move_line_row,
                            move_line_col + 0,
                            move_line.move_id
                            and move_line.move_id.name
                            or "",
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 1,
                            move_line.move_id
                            and MOVE_TYPES[move_line.move_id.move_type]
                            or "",
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 2,
                            move_line.partner_id
                            and move_line.partner_id.ref or move_line.partner_id.name
                            or ""
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 3,
                            move_line.account_id
                            and move_line.account_id.code
                            or ""
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 4,
                            move_line.date
                            and move_line.date
                            or "",
                            date_format,
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 5,
                            move_line.move_id
                            and move_line.move_id.ref
                            or "",
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 6,
                            move_line.tax_base_amount
                            and float(move_line.tax_base_amount)
                            or "",
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 7,
                            move_line.amount_currency
                            and float(abs(move_line.amount_currency))
                        )
                        sheet.write(
                            move_line_row, move_line_col + 8, tax_from_base_amount or "0",
                        )
                        sheet.write(
                            move_line_row,
                            move_line_col + 9,
                            move_line.tax_line_id
                            and move_line.tax_line_id.description
                            or "",
                        )
                        move_line_row = move_line_row + 1
                        count += 1
        if count <= 0:
            raise MissingError(_('Nothing to print !'))


class MoveLinePossibleDuplicateTaxXLSX(models.AbstractModel):
    _name = "report.report_xlsx.move_line_possible_duplicate_tax_xlsx"
    _description = "xlsx report"
    _inherit = "report.report_xlsx.abstract"

    def find_duplicates(self, lst, keys):
        freq = {}
        for d in lst:
            k = tuple(d[k] for k in keys)
            freq[k] = freq.get(k, 0) + 1
        return [d for d in lst if freq[tuple(d[k] for k in keys)] > 1]

    def generate_xlsx_report(self, workbook, data, move_lines):
        # Create a new worksheet
        sheet = workbook.add_worksheet('Possible Duplicate Entries')
        move_line_row = 0
        move_line_col = 0
        count = 0
        # Write the header row to the worksheet
        # Add the header row to the worksheet
        bold = workbook.add_format({'bold': True})
        sheet.write('A1', 'No', bold)
        sheet.write('B1', 'Type', bold)
        sheet.write('C1', 'Ref', bold)
        sheet.write('D1', 'Account', bold)
        sheet.write('E1', 'Nominal', bold)
        sheet.write('F1', 'Date', bold)
        sheet.write('G1', 'Net Amount', bold)
        sheet.write('H1', 'Tax Amount', bold)
        sheet.write('I1', 'Tax Code', bold)
        move_line_row += 1
        unique_month_year = set()
        move_lines_dict_lists = [{'move_line_id': move_line, 'no': move_line.move_id and move_line.move_id.name or '',
                                  'ref': move_line.move_id and move_line.move_id.ref or '',
                                  'account': move_line.partner_id and move_line.partner_id.ref or '',
                                  'nominal': move_line.account_id and move_line.account_id.code or '',
                                  'date': move_line.date and move_line.date or '',
                                  'net_amount': move_line.tax_base_amount and float(move_line.tax_base_amount) or '',
                                  'tax_amount': move_line.amount_currency and float(
                                      abs(move_line.amount_currency)) or '',
                                  'tax_code': move_line.tax_line_id and move_line.tax_line_id.description or ''} for
                                 move_line in
                                 move_lines.sudo()]

        move_lines_duplicate_lists = self.find_duplicates(move_lines_dict_lists,
                                                          ['ref', 'account', 'nominal', 'date', 'net_amount',
                                                           'tax_amount', 'tax_code'])
        move_line_ids = [move_lines_duplicate_list['move_line_id'].id for move_lines_duplicate_list in
                         move_lines_duplicate_lists]
        for move_line in move_lines.filtered(lambda l: l.id in move_line_ids):
            unique_month_year.add((move_line.date.strftime('%B'), move_line.date.year))
            if move_line.amount_currency:
                report_name = "Unexpected Tax Report for " + str(unique_month_year)
                date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
                sheet.write(
                    move_line_row,
                    move_line_col + 0,
                    move_line.move_id
                    and move_line.move_id.name
                    or "",
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 1,
                    move_line.move_id.move_type
                    and MOVE_TYPES[move_line.move_id.move_type]
                    or "",
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 2,
                    move_line.move_id
                    and move_line.move_id.ref
                    or "",
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 3,
                    move_line.partner_id
                    and move_line.partner_id.ref or move_line.partner_id.name
                    or ""
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 4,
                    move_line.account_id
                    and move_line.account_id.code
                    or "",
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 5,
                    move_line.date
                    and move_line.date
                    or "",
                    date_format,
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 6,
                    move_line.tax_base_amount
                    and float(move_line.tax_base_amount)
                    or "",
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 7,
                    move_line.amount_currency
                    and float(abs(move_line.amount_currency))
                )
                sheet.write(
                    move_line_row,
                    move_line_col + 8,
                    move_line.tax_line_id
                    and move_line.tax_line_id.description
                    or "",
                )
                move_line_row = move_line_row + 1
                count += 1
        if count <= 0:
            raise MissingError(_('Nothing to print !'))
