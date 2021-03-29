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

    @api.depends('move_reconciled','move_line_ids.reconciled')
    def move_reconciled_store(self):
        for payment in self:
            payment.store_move_reconciled = payment.move_reconciled

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

            state = ['posted','reconciled']
            args += [('partner_id','=',partner_id),('partner_type','=',partner_type),
            ('state','in',state),('store_move_reconciled','=',False)]

        return super(AccontPayment, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)



    def _prepare_payment_moves(self):
        ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
        to the 'create' method.

        Example 1: outbound with write-off:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |   900.0   |
        RECEIVABLE          |           |   1000.0
        WRITE-OFF ACCOUNT   |   100.0   |

        Example 2: internal transfer from BANK to CASH:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |           |   1000.0
        TRANSFER            |   1000.0  |
        CASH                |   1000.0  |
        TRANSFER            |           |   1000.0

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        ''' 
        

        if self._context.get('amount_to_pay') or self._context.get('amount_remain'):
            all_move_vals = []
            for payment in self:
                company_currency = payment.company_id.currency_id
                move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

                if self._context.get('amount_to_pay'):
                    amount = self._context.get('amount_to_pay')
                    in_payment = True
                else:
                    amount = self._context.get('amount_remain')
                    in_payment = False

                payment_type = self._context.get('payment_type')

                currency_id = self._context.get('currency_id', False)
               
                
                # Compute amounts.
                write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
                if payment.payment_type in ('outbound', 'transfer') or payment.payment_type == payment_type:
                    counterpart_amount = amount
                    liquidity_line_account = payment.journal_id.default_debit_account_id
                else:
                    counterpart_amount = -amount
                    liquidity_line_account = payment.journal_id.default_credit_account_id

               
                # Manage currency.
                if currency_id and currency_id != company_currency:
                    balance = currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                    write_off_balance = currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                    currency_id = currency_id.id
                    
                elif currency_id == company_currency:
                    # Single-currency.
                    balance = counterpart_amount
                    write_off_balance = write_off_amount
                    counterpart_amount = write_off_amount = 0.0
                    currency_id = False
               
                else:
                    # Multi-currencies.
                    balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                    write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                    currency_id = payment.currency_id.id
                 
                # Manage custom currency on journal for liquidity line.
                if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                    # Custom currency on journal.
                    if payment.journal_id.currency_id == company_currency:
                        # Single-currency
                        liquidity_line_currency_id = False
                    else:
                        liquidity_line_currency_id = payment.journal_id.currency_id.id
                    liquidity_amount = company_currency._convert(
                        balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
                elif self._context.get('currency_id'):
                    liquidity_line_currency_id = self._context.get('currency_id').id
                    liquidity_amount = company_currency._convert(
                        balance, self._context.get('currency_id'), payment.company_id, payment.payment_date)
                else:
                    # Use the payment currency.
                    liquidity_line_currency_id = currency_id
                    liquidity_amount = counterpart_amount

               
                # Compute 'name' to be used in receivable/payable line.

                # 5/0

                rec_pay_line_name = ''
                if payment.payment_type == 'transfer':
                    rec_pay_line_name = payment.name
                else:
                    if payment.partner_type == 'customer':
                        if payment.payment_type == 'inbound':
                            rec_pay_line_name += _("Customer Payment")
                        elif payment.payment_type == 'outbound':
                            rec_pay_line_name += _("Customer Credit Note")
                    elif payment.partner_type == 'supplier':
                        if payment.payment_type == 'inbound':
                            rec_pay_line_name += _("Vendor Credit Note")
                        elif payment.payment_type == 'outbound':
                            rec_pay_line_name += _("Vendor Payment")
                    if payment.invoice_ids:
                        rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

                # Compute 'name' to be used in liquidity line.
                if payment.payment_type == 'transfer':
                    liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
                else:
                    liquidity_line_name = payment.name

                # ==== 'inbound' / 'outbound' ====

                if not payment.partner_id:
                    partner_id = self._context.get('partner_id').id
                else:
                    partner_id = payment.partner_id.id

                if self._context.get('account_id'):
                    account_id = self._context.get('account_id')
                else:
                    account_id = payment.destination_account_id.id

                move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'journal_id': payment.journal_id.id,
                    'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                    'partner_id': payment.partner_id.id,
                    'line_ids': [
                        # Receivable / Payable / Transfer line.
                        (0, 0, {
                            'name': rec_pay_line_name,
                            'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                            'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': partner_id or False,
                            'account_id': account_id,
                            'payment_id': payment.id,
                            'in_payment': in_payment,
                            'last_line_number' : int(self._context.get('last_line_number', 0)),
                        }),
                
                    ],
                }
                if write_off_balance:
                    # Write-off line.
                    move_vals['line_ids'].append((0, 0, {
                        'name': payment.writeoff_label,
                        'amount_currency': -write_off_amount,
                        'currency_id': currency_id,
                        'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                        'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.writeoff_account_id.id,
                        'payment_id': payment.id,
                    }))

                if move_names:
                    move_vals['name'] = move_names[0]

                all_move_vals.append(move_vals)


                # ==== 'transfer' ====
                if payment.payment_type == 'transfer':
                    journal = payment.destination_journal_id

                    # Manage custom currency on journal for liquidity line.
                    if journal.currency_id and payment.currency_id != journal.currency_id:
                        # Custom currency on journal.
                        liquidity_line_currency_id = journal.currency_id.id
                        transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)
                    else:
                        # Use the payment currency.
                        liquidity_line_currency_id = currency_id
                        transfer_amount = counterpart_amount

                    transfer_move_vals = {
                        'date': payment.payment_date,
                        'ref': payment.communication,
                        'partner_id': payment.partner_id.id,
                        'journal_id': payment.destination_journal_id.id,
                        'line_ids': [
                            # Transfer debit line.
                            (0, 0, {
                                'name': payment.name,
                                'amount_currency': -counterpart_amount if currency_id else 0.0,
                                'currency_id': currency_id,
                                'debit': balance < 0.0 and -balance or 0.0,
                                'credit': balance > 0.0 and balance or 0.0,
                                'date_maturity': payment.payment_date,
                                'partner_id': payment.partner_id.commercial_partner_id.id,
                                'account_id': payment.company_id.transfer_account_id.id,
                                'payment_id': payment.id,
                            }),
                            # Liquidity credit line.
                            (0, 0, {
                                'name': _('Transfer from %s') % payment.journal_id.name,
                                'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                                'currency_id': liquidity_line_currency_id,
                                'debit': balance > 0.0 and balance or 0.0,
                                'credit': balance < 0.0 and -balance or 0.0,
                                'date_maturity': payment.payment_date,
                                'partner_id': payment.partner_id.commercial_partner_id.id,
                                'account_id': payment.destination_journal_id.default_credit_account_id.id,
                                'payment_id': payment.id,
                            }),
                        ],
                    }

                    if move_names and len(move_names) == 2:
                        transfer_move_vals['name'] = move_names[1]

                    all_move_vals.append(transfer_move_vals)
            return all_move_vals
        else:
            return super(AccontPayment, self)._prepare_payment_moves()
            

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and credit notes) and/or new move lines (eg. write-offs).
            If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
            items, as well as a journal item for the bank statement line.
            Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.

            :param self: browse collection of records that are supposed to have no accounting entries already linked.
            :param (list of dicts) counterpart_aml_dicts: move lines to create to reconcile with existing payables/receivables.
                The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'move_line'
                    # The move line to reconcile (partially if specified debit/credit is lower than move line's credit/debit)

            :param (list of recordsets) payment_aml_rec: recordset move lines representing existing payments (which are already fully reconciled)

            :param (list of dicts) new_aml_dicts: move lines to create. The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'account_id'
                - (optional) 'tax_ids'
                - (optional) Other account.move.line fields like analytic_account_id or analytics_id
                - (optional) 'reconcile_model_id'

            :returns: The journal entries with which the transaction was matched. If there was at least an entry in counterpart_aml_dicts or new_aml_dicts, this list contains
                the move created by the reconciliation, containing entries for the statement.line (1), the counterpart move lines (0..*) and the new move lines (0..*).
        """
        payable_account_type = self.env.ref('account.data_account_type_payable')
        receivable_account_type = self.env.ref('account.data_account_type_receivable')
        suspense_moves_mode = self._context.get('suspense_moves_mode')
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env['account.move.line']
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env['account.move.line']

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        counterpart_moves = self.env['account.move']

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_('A selected move line was already reconciled.'))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled and not suspense_moves_mode:
                raise UserError(_('A selected move line was already reconciled.'))
            if isinstance(aml_dict['move_line'], int):
                aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])

        account_types = self.env['account.account.type']
        for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
            if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], int):
                # Transform the value in the format required for One2many and Many2many fields
                aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]

            user_type_id = self.env['account.account'].browse(aml_dict.get('account_id')).user_type_id
            if user_type_id in [payable_account_type, receivable_account_type] and user_type_id not in account_types:
                account_types |= user_type_id
        if suspense_moves_mode:
            if any(not line.journal_entry_ids for line in self):
                raise UserError(_('Some selected statement line were not already reconciled with an account move.'))
        else:
            if any(line.journal_entry_ids for line in self):
                raise UserError(_('A selected statement line was already reconciled with an account move.'))

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount
        currency = self.currency_id or statement_currency
        for aml_rec in payment_aml_rec:
            balance = aml_rec.amount_currency if aml_rec.currency_id else aml_rec.balance
            aml_currency = aml_rec.currency_id or aml_rec.company_currency_id
            total -= aml_currency._convert(balance, currency, aml_rec.company_id, aml_rec.date)
            aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
            counterpart_moves = (counterpart_moves | aml_rec.move_id)
            if aml_rec.journal_id.post_at == 'bank_rec' and aml_rec.payment_id and aml_rec.move_id.state == 'draft':
                # In case the journal is set to only post payments when performing bank
                # reconciliation, we modify its date and post it.
                aml_rec.move_id.date = self.date
                aml_rec.payment_id.payment_date = self.date
                aml_rec.move_id.post()
                # We check the paid status of the invoices reconciled with this payment
                for invoice in aml_rec.payment_id.reconciled_invoice_ids:
                    self._check_invoice_state(invoice)

        # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
        # case we reconcile the existing and the new move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            if suspense_moves_mode:
                self.button_cancel_reconciliation()
            move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
            counterpart_moves = (counterpart_moves | move)

            # Create The payment
            payment = self.env['account.payment']
            partner_id = self.partner_id or (aml_dict.get('move_line') and aml_dict['move_line'].partner_id) or self.env['res.partner']
    
            if abs(total)>0.00001:
                payment_vals = self._prepare_payment_vals(total)

                if not payment_vals['partner_id']:
                    payment_vals['partner_id'] = partner_id.id
                    payment_vals['partner_type'] = 'customer' if account_types == receivable_account_type else 'supplier'
                if payment_vals['partner_id'] and len(account_types) == 1:
                    payment_vals['partner_type'] = 'customer' if account_types == receivable_account_type else 'supplier'

                payment = payment.create(payment_vals)

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = (counterpart_aml_dicts + new_aml_dicts)
            date = self.date or fields.Date.today()
            for aml_dict in to_create:
                aml_dict['move_id'] = move.id
                aml_dict['partner_id'] = self.partner_id.id
                aml_dict['statement_line_id'] = self.id

                if aml_dict.get('manual_partner_id'):
                    aml_dict['partner_id'] = aml_dict.get('manual_partner_id')
                    aml_dict.pop('manual_partner_id')

                self._prepare_move_line_for_currency(aml_dict, date)

            partner_ids = []

            # Create write-offs
            for aml_dict in new_aml_dicts:
                aml_dict['payment_id'] = payment and payment.id or False
                if aml_dict['partner_id']:
                    if aml_dict['partner_id'] not in partner_ids:
                        partner_ids.append(aml_dict['partner_id'])
                aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if aml_dict['move_line'].payment_id and not aml_dict['move_line'].statement_line_id:
                    aml_dict['move_line'].write({'statement_line_id': self.id})
                if aml_dict['move_line'].partner_id.id:
                    aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
                aml_dict['account_id'] = aml_dict['move_line'].account_id.id
                aml_dict['payment_id'] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop('move_line')
                new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)

                (new_aml | counterpart_move_line).reconcile()

                self._check_invoice_state(counterpart_move_line.move_id)

            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict['payment_id'] = payment and payment.id or False
            if not aml_dict['partner_id']:
                if move.line_ids[0].partner_id:
                    aml_dict['partner_id'] = move.line_ids[0].partner_id and move.line_ids[0].partner_id.id or False

            aml_obj.with_context(check_move_validity=False).create(aml_dict)

            move.post()
            #record the move name on the statement line to be able to retrieve it in case of unreconciliation
            self.write({'move_name': move.name})
            payment and payment.write({'payment_reference': move.name})
        elif self.move_name:
            raise UserError(_('Operation not allowed. Since your statement line already received a number (%s), you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.') % (self.move_name))

        #create the res.partner.bank if needed
        if self.account_number and self.partner_id and not self.bank_account_id:
            # Search bank account without partner to handle the case the res.partner.bank already exists but is set
            # on a different partner.
            self.bank_account_id = self._find_or_create_bank_account()

        counterpart_moves._check_balanced()
        return counterpart_moves