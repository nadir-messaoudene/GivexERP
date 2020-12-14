# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# pylint: disable=W1505
import base64
from codecs import BOM_UTF8

from odoo import _, api, models

BOM_UTF8U = BOM_UTF8.decode('UTF-8')
CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def generate_xml_attachment(self):
        self.ensure_one()
        if not self.l10n_mx_edi_cfdi:
            return False
        fname = ("%s-%s-MX-Bill-%s.xml" % (
            self.journal_id.code, self.invoice_payment_ref,
            self.company_id.partner_id.vat or '')).replace('/', '')
        data_attach = {
            'name': fname,
            'datas': base64.encodestring(
                self.l10n_mx_edi_cfdi and
                self.l10n_mx_edi_cfdi.lstrip() or ''),
            'description': _('XML signed from Invoice %s.') % self.name,
            'res_model': self._name,
            'res_id': self.id,
        }
        self.l10n_mx_edi_cfdi_name = fname
        res = self.env['ir.attachment'].with_context({}).create(data_attach)
        if self._context.get('l10n_mx_edi_invoice_type') == 'out':
            self.l10n_mx_edi_pac_status = 'signed'
        return res

    def create_adjustment_line(self, xml_amount):
        """If the invoice has difference with the total in the CFDI is
        generated a new line with that adjustment if is found the account to
        assign in this lines. The account is assigned in a system parameter
        called 'adjustment_line_account_MX'"""
        account_id = self.env['ir.config_parameter'].sudo().get_param(
            'adjustment_line_account_MX', '')
        if not account_id:
            return False
        self.invoice_line_ids.create({
            'account_id': account_id,
            'name': _('Adjustment line'),
            'quantity': 1,
            'price_unit': xml_amount - self.amount_total,
            'invoice_id': self.id,
        })
        return True

    def post(self):
        if self._context.get('l10n_mx_edi_invoice_type') == 'out':
            attach_invoices = self.filtered(
                lambda inv: inv.state == 'draft' and inv.l10n_mx_edi_pac_status == 'signed')
            attachs = [(inv, inv.l10n_mx_edi_retrieve_last_attachment()) for inv in attach_invoices]
            res = super().post()
            for inv, att in attachs:
                att.name = inv.l10n_mx_edi_cfdi_name
            return res
        # Sync SAT status if not set yet (Vendor Bills)
        res = super(AccountInvoice, self).post()
        vendor_bills = self.filtered(lambda inv: inv.is_purchase_document() and inv.l10n_mx_edi_cfdi_name)
        vendor_bills.l10n_mx_edi_update_sat_status()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _default_account(self):
        """This method was forwardported from v12, please take
        extra care reviewing it.
        """
        if self._context.get('journal_id'):
            journal = self.env['account.journal'].browse(
                self._context.get('journal_id'))
            if self._context.get('type') in ('out_invoice', 'in_refund'):
                return journal.default_credit_account_id.id
            return journal.default_debit_account_id.id
