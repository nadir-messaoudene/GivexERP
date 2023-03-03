# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date

import time
import math
import base64



class AccontPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('is_reconciled','move_id.line_ids.reconciled')
    def move_reconciled_store(self):
        for payment in self:
            payment.store_move_reconciled = payment.is_reconciled

    store_move_reconciled = fields.Boolean('Reconciled Move', compute="move_reconciled_store", store=True, copy=False)
    last_amount = fields.Float('Last Amount', default=0.00)
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if self._context.get('partner_id') and self._context.get('partner_type'):
            partner_id = int(self._context.get('partner_id'))
            if self._context.get('partner_type') == 'customer':
                partner_type = 'customer'
            else:
                partner_type = 'supplier'

            args += [('partner_id','=',partner_id),('partner_type','=',partner_type),
            ('state','=','posted'),('store_move_reconciled','=',False)]

        return super(AccontPayment, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        if self._context.get('amount_to_pay') or self._context.get('amount_remain'):

            self.ensure_one()
            write_off_line_vals = write_off_line_vals or {}

            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                    self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self._context.get('amount_to_pay'):
                amount = self._context.get('amount_to_pay')
                in_payment = True
            else:
                amount = self._context.get('amount_remain')
                in_payment = False

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0

            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else:
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )

            line_vals_list = [
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                    'in_payment': in_payment,
                    'last_line_number' : int(self._context.get('last_line_number', 0)),
                },
            ]
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
            return line_vals_list 
        else:
            return super(AccontPayment, self)._prepare_move_line_default_vals(False)