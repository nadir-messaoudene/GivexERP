# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.http import request
from ..models.clover_request import CloverRequest
import pprint, json, random, string, requests
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    use_clover_terminal = fields.Boolean()
    clover_device_id = fields.Many2one(comodel_name='clover.device')
    support_clover_terminal = fields.Boolean(compute='compute_support_clover_terminal', default=False)
    payment_type_inbound = fields.Boolean()
    payment_type_outbound = fields.Boolean()
    clover_payment_status = fields.Selection(
        string='Clover Payment Status',
        selection=[
            ('pending', 'Pending'),
            ('waiting', 'Waiting'),
            ('done', 'Done'),
            ('retry', 'Retry'),
            ('waitingCancel', 'Waiting Cancel'),
            ('reversing', 'Reversing'),
            ('reversed', 'Reversed'),
        ], default='pending'
    )
    clover_move_name = fields.Char()
    clover_x_pos_id = fields.Char('POS Id', related='clover_device_id.x_pos_id', readonly="1")
    clover_idempotency_id = fields.Char()

    
    @api.depends('journal_id')
    def compute_support_clover_terminal(self):
        self.support_clover_terminal = self.journal_id.use_clover_terminal
        

    @api.onchange('group_payment')
    def _onchange_cl_group_payment(self):
        _logger.info("\n _onchange_group_payment")
        for rec in self:
            rec.clover_move_name = ""
            if rec.group_payment == True and len(rec.line_ids.move_id) > 1:
                flag = False
                for line in rec.line_ids.move_id:
                    rec.clover_move_name += line.name if flag == False else "," + line.name
                    flag = True

        _logger.info("\n--------------\n _onchange_group_payment: " +
                     rec.clover_move_name + "\n-----------")

    @api.onchange('journal_id')
    def _onchange_cl_journal_id(self):
        _logger.info("\n _onchange_cl_journal_id")
        for rec in self:
            rec.clover_move_name = ""
            if rec.group_payment == False and len(rec.line_ids.move_id) == 1:
                rec.clover_move_name = rec.line_ids.move_id.name
            if rec.group_payment == True and len(rec.line_ids.move_id) > 1:
                flag = False
                for line in rec.line_ids.move_id:
                    rec.clover_move_name += line.name if flag == False else "," + line.name
                    flag = True

            _logger.info("\n--------------\n _onchange_group_payment: " +
                         rec.clover_move_name + "\n-----------")

            rec.use_clover_terminal = rec.support_clover_terminal = rec.payment_type_inbound = False
            if rec.journal_id and rec.journal_id.use_clover_terminal:
                rec.use_clover_terminal = True
                rec.support_clover_terminal = True
                rec.payment_type_inbound = bool(rec.payment_type == 'inbound')
                rec.payment_type_outbound = bool(rec.payment_type == 'outbound')


    @api.onchange('amount')
    def _onchange_amount(self):
        _logger.info("\n_onchange_journal_amt")
        for rec in self:

            amount_residual_signed = sum(rec.line_ids.move_id.filtered(
                lambda r: r.state == "posted").mapped("amount_residual_signed"))
            _logger.info("\namount_residual_signed: %.2f, amount: %.2f" %
                         (amount_residual_signed, rec.amount))

            if rec.journal_id and rec.journal_id.use_clover_terminal == True and \
                    rec.payment_method_line_id.code == 'electronic':

                # Invoice Payment Check
                if rec.payment_type == 'inbound' and rec.amount > amount_residual_signed:
                    raise UserError(_("You can not pay with this amount." +
                                      "\nPayment Amount: %s%s,\nInvoice Due: %s %s" % (rec.currency_id.symbol, "{:.2f}".format(rec.amount), rec.currency_id.symbol, "{:.2f}".format(amount_residual_signed))))
                # Credit Note Payment Check
                if rec.payment_type == 'outbound' and rec.amount > abs(amount_residual_signed):
                    raise UserError(_("You can not refund with this amount." +
                                      "\nPayment Amount: %s - %s,\nCredit Note Due Amount: %s %s" % (rec.currency_id.symbol, "{:.2f}".format(rec.amount), rec.currency_id.symbol, "{:.2f}".format(amount_residual_signed))))

    def action_create_payments(self):
        _logger.info("action_create_payments ===>>>>>")
        if self.journal_id.use_clover_terminal and not self.payment_token_id:
            self.action_send_clover_payment()

            record = self
            payments = record._create_payments()

            # ----------------------------------------------------------
            context = dict(record.env.context)
            if len(payments) > 0 and context.get('cloverResponse'):
                _logger.info("payments-->" +str(payments))
                record._update_clover_values(payments, record.env.context)
            # ----------------------------------------------------------


            if record._context.get('dont_redirect_to_payments'):
                return True

            action = {
                'name': _('Payments'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'context': {'create': False},
            }
            if len(payments) == 1:
                action.update({
                    'view_mode': 'form',
                    'res_id': payments.id,
                })
            else:
                action.update({
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', payments.ids)],
                })
            return action
        else:
            return super(AccountPaymentRegister,self).action_create_payments()

    def _update_clover_values(self, payments, context):
        if self.journal_id.use_clover_terminal == True:
            if self.group_payment == True and len(self.line_ids.move_id) > 1:
                move_name = self.clover_move_name or payments.ref

            if len(self.line_ids.move_id) == 1:
                move_name = self.clover_move_name or payments.ref
                move_name = move_name.split(
                    ": ")[1] if ": " in move_name else move_name
                move_name = move_name.split(
                    ",")[0] if "," in move_name else move_name

            if context.get('cloverResponse'):
                _logger.info('\n Clover Terminal Response\n' +
                             str(context.get('cloverResponse')))

                if len(payments) == 1:
                    account_move = request.env['account.move'].sudo()
                    response = context.get('cloverResponse')
                    active_id = context.get('active_id') or context.get('active_ids')
                    accMove = account_move.search([('id', '=', active_id)])

                    if len(accMove) > 0:
                        _logger.info("accMove" + str(accMove) +
                                     "\n clover_last_action--->" + str(accMove[0].clover_last_action))

                        action = 'PURCHASE'
                        if accMove[0].clover_last_action == 'PURCHASE':
                            action = 'PURCHASE'
                        if accMove[0].clover_last_action == 'REFUND':
                            action = 'REFUND'

                        try:
                            data = response.get('data', {})
                            payment_vals = self._get_payment_vals(payments, action, move_name, data)
                            _logger.info("payment_vals" + str(payment_vals))
                            payments.write(payment_vals)
                        except Exception as e:
                            payments.write({'clover_response': json.dumps(response)})
                            _logger.warning(str(e.args))

    def _get_payment_vals(self, payments, action, move_name, response):
        """
            param: payments     `account.payment`
            param: action       `PURCHASE or RETURN or VOID`
            param: move_name    action `account.move` name
            param" response     response from Clover Terminal
            return payment_vals `a dict containing payment values`
        """
        payment_vals = {}
        if response.get("payment"):
            action = "PURCHASE"
            dpayment = response.get("payment", {})
            cardTransaction = dpayment.get("cardTransaction", {})
            vaultedCard = cardTransaction.get("vaultedCard", {})
            clover_amount = "{:0.2f}".format(
                int(dpayment.get("amount"))/100) if dpayment.get("amount") else False

            _logger.info("\ndpayment\n" + pprint.pformat(dpayment))
            _logger.info("\ncardTransaction\n" + pprint.pformat(cardTransaction))
            _logger.info("\nvaultedCard\n" + pprint.pformat(vaultedCard))
            _logger.info("clover_amount-->" + clover_amount)

            paidamt = str(payments.amount*100)
            paidamt = paidamt.split(
                ".")[0] if "." in paidamt else str(payments.amount*100)

            if action == "REFUND" or action == "PURCHASE":
                ter_amt = str(dpayment.get("amount"))

            _logger.info(
                "\n action--->" + str(action) +
                "\n paidamt--->" + str(paidamt) +
                "\n ter_amt--->" + str(ter_amt) +
                "\n payments.ref--->" + str(payments.ref) +
                "\n invoice_origin--->" + str(payments.invoice_origin) +
                "\n invoice_name--->" + str(payments.move_id.name) +
                "\n move_name--->" + str(move_name) +
                "\n clover_move_name--->" + str(self.clover_move_name)
            )

            if payments.journal_id.use_clover_terminal == True:
                _logger.info(
                    "use_clover_terminal--->" + str(payments.journal_id.use_clover_terminal))
                if paidamt == ter_amt:
                    _logger.info("Amount Matches")

                payment_vals = {
                    'clover_success': response.get("success"),
                    'clover_result': response.get("result"),
                    'clover_payment_id': dpayment.get("id", ""),
                    'clover_order_id':  dpayment.get("order", {}).get("id", ""),
                    'clover_tender_id': dpayment.get("tender", {}).get("id", ""),
                    'clover_amount': clover_amount,
                    'clover_ext_id': dpayment.get("externalPaymentId"),
                    'clover_emp_id': dpayment.get("employee", {}).get("id", ""),
                    'clover_created_time': dpayment.get("createdTime"),
                    'clover_payment_result': dpayment.get("result"),
                    # cardTransaction
                    'clover_card_type': cardTransaction.get("cardType"),
                    'clover_entry_type': cardTransaction.get("entryType"),
                    'clover_type': cardTransaction.get("type"),
                    'clover_auth_code': cardTransaction.get("authCode"),
                    'clover_reference_id': cardTransaction.get("referenceId"),
                    'clover_transaction_no': cardTransaction.get("transactionNo"),
                    'clover_state': cardTransaction.get("state"),
                    # vaultedCard
                    'clover_last_digits': vaultedCard.get("last4"),
                    'clover_cardholder_name': vaultedCard.get("cardholderName"),
                    'clover_expiry_date': vaultedCard.get("expirationDate"),
                    'clover_token': vaultedCard.get("token"),
                }
                _logger.info("payment_vals" + str(payment_vals))

        if response.get("refund"):
            action = "REFUND"
            ter_amt = "0"
            refund = response.get("refund", {})
            clover_amount = "{:0.2f}".format(
                int(refund.get("amount"))/100) if refund.get("amount") else False
            taxAmount = "{:0.2f}".format(
                int(refund.get("taxAmount"))/100) if refund.get("taxAmount") else False
            paidamt = str(payments.amount*100)
            paidamt = paidamt.split(
                ".")[0] if "." in paidamt else str(payments.amount*100)

            _logger.info("\nrefund\n" + pprint.pformat(refund))
            _logger.info("clover_amount-->" + clover_amount)
            _logger.info("paidamt-->" + paidamt)

            if action == "REFUND" or action == "PURCHASE":
                ter_amt = str(refund.get("amount"))

            _logger.info(
                "\n action--->" + str(action) +
                "\n paidamt--->" + str(paidamt) +
                "\n ter_amt--->" + str(ter_amt) +
                "\n payments.ref--->" + str(payments.ref) +
                "\n invoice_origin--->" + str(payments.invoice_origin) +
                "\n invoice_name--->" + str(payments.move_id.name) +
                "\n move_name--->" + str(move_name) +
                "\n clover_move_name--->" + str(self.clover_move_name)
            )

            if payments.journal_id.use_clover_terminal == True:
                _logger.info(
                    "use_clover_terminal--->" + str(payments.journal_id.use_clover_terminal))
                if paidamt == ter_amt:
                    _logger.info("Amount Matches")

                payment_vals = {
                    'clover_success': response.get("success"),
                    'clover_result': response.get("result"),
                    'clover_refund_reason': response.get("reason"),
                    'clover_message': response.get("message"),
                    'clover_order_id':  response.get("orderId", ""),
                    'clover_payment_id': response.get("paymentId", ""),
                    # Refund Object
                    'clover_refund_id': refund.get("id", ""),
                    'clover_device_id': refund.get("device", {}).get("id", ""),
                    'clover_amount': clover_amount,
                    'clover_tax_amount': taxAmount,
                    'clover_created_time': refund.get("createdTime"),
                    'clover_client_created_time': refund.get("clientCreatedTime"),
                    'clover_emp_id': refund.get("employee", {}).get("id", ""),
                    'clover_voided': refund.get("voided", ""),
                    'clover_transaction_info': refund.get("transactionInfo"),
                }

        return payment_vals

    clover_order_id = fields.Char()
    clover_payment_id = fields.Char()

    @api.onchange('journal_id','use_clover_terminal')
    def _compute_move_orderpay(self):
        for rec in self:
            if rec.journal_id.use_clover_terminal == True and rec.payment_type == 'outbound' \
                    and rec.use_clover_terminal:
                comm = rec.communication
                if comm:
                    inv_names = comm.split("Reversal of: ")
                    if len(inv_names) > 1:
                        inv_name = inv_names[1].split(",")[0]
                        _logger.info("inv_name--->" + inv_name)
                        AccPaymnt = self.env['account.payment']
                        pay_id = AccPaymnt.sudo().search(
                            [('move_id.ref', '=', inv_name)])
                        if pay_id:
                            _logger.info("clover_order_id" +
                                         str(pay_id.clover_order_id))
                            _logger.info("clover_payment_id" +
                                         str(pay_id.clover_payment_id))
                            rec.clover_order_id = pay_id.clover_order_id
                            rec.clover_payment_id = pay_id.clover_payment_id


    def clover_validation(self):
        if self.journal_id.use_clover_terminal and self.use_clover_terminal:
            if not self.clover_device_id:
                raise UserError(_("Clover Device is not selected...."))
            if not self.clover_x_pos_id:
                raise UserError(
                    _("POS ID is not updated for the Device-{}".format(self.clover_device_id.serial)))
            if not self.journal_id.clover_config_id:
                raise UserError(
                    _("Config ID is not updated for the Device-{}".format(self.clover_device_id.serial)))


    def action_send_clover_payment(self):
        self.clover_validation()
        clover_payment = {'success' : False}
        
        if self.journal_id.use_clover_terminal and self.use_clover_terminal:
            try:
                context = dict(self.env.context)
                if self.communication and context.get('active_ids'):
                    move_id = request.env['account.move'].sudo().browse(context.get('active_ids'))

                    self._compute_move_orderpay()
                    print("clover_order_id ===>>>{}".format(self.clover_order_id))
                    print("clover_payment_id ===>>>{}".format(self.clover_payment_id))

                    if move_id.move_type == 'out_refund' and not self.clover_order_id and not self.clover_payment_id:
                        raise UserError(_("Clover Order and Clover Payment must be provided for Credit Note Payments"))


                    amount = int(self.amount*100)
                    print("amount ===>>>{}".format(amount))

                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "X-Clover-Device-Id": self.clover_device_id.serial,
                        "X-POS-Id": self.clover_x_pos_id,
                        "Authorization": "Bearer " + self.journal_id.clover_jwt_token,
                    }

                    payload = {
                        'configId': self.journal_id.clover_config_id,
                        'deviceId': self.clover_device_id.serial,
                        'posId': self.clover_x_pos_id,
                        'idempotencyId': self.communication,
                        'amount': amount,
                        'externalPaymentId': self.communication,
                    }

                    values = {
                        'headers' : headers,
                        'payload' : payload,
                        'clover_order_id' : self.communication,
                        'order_name' : self.communication,
                    }

                    if not self.clover_idempotency_id:
                        idempotencyId = self.get_idempotency_id(values=payload)
                        self.clover_idempotency_id = idempotencyId
                        payload.update({'idempotencyId' : idempotencyId})
                        try:
                            self._cr.commit()
                        except Exception as e:
                            _logger.error("Exception: {}".format(e.args))



                    payload = values['payload']
                    payload.update({
                        'cloverJwtToken': self.journal_id.clover_jwt_token,
                        'cloverServerUrl': self.journal_id.clover_server_url,
                    })
                    if move_id.move_type == 'out_refund':
                        values.update({
                            'clover_order_id' : self.clover_order_id,
                            'clover_payment_id' : self.clover_payment_id
                        })

                    if context.get('active_id'):
                        move_id = self.env['account.move'].browse(int(context.get('active_id')))
                        values.update({'move_type':move_id.move_type})
                        payload.update({
                            'move_type':move_id.move_type,
                            "method": 'EMAIL',
                            "email": move_id.partner_id.email or '',
                            "phone": move_id.partner_id.phone or '',
                            "move_id" : move_id,
                        })

                        if move_id.move_type == 'out_refund':
                            payload.update({
                                'clover_order_id' : self.clover_order_id,
                                'clover_payment_id' : self.clover_payment_id
                            })

                    cpr = CloverRequest(debug_logger=True, values=payload)
                    clover_payment = cpr.action_send_clover_payment(values=payload)

                    if clover_payment and not clover_payment.get('success'):
                        raise UserError(_(clover_payment.get('err', {})))


                return clover_payment
            except Exception as e:
                if hasattr(e,"name"):
                    raise UserError(_("Terminal Response: {}".format(e.name or "Multiple Internal Error")))
                else:
                    raise UserError(_("Error Response: {}".format(e.args or "Multiple Internal Error")))


    def get_idempotency_id(self, values):
        idempotencyId = values.get('idempotencyId') + ''.join(random.choices(string.ascii_lowercase, k=5))
        print("idempotencyId ===>>>{}".format(idempotencyId))
        return idempotencyId