# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import pprint
import json
import pytz

from odoo.addons.odoosync_base.utils.app_payment import AppPayment

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    use_cloud_terminal = fields.Boolean(string="Use cloud terminal")
    support_mcloud_terminal = fields.Boolean()
    payment_type_inbound = fields.Boolean()
    payment_type_outbound = fields.Boolean()
    moneris_payment_status = fields.Selection(
        string='Payment Status',
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
    moneris_move_name = fields.Char(compute='_onchange_journal_id')

    moneris_is_manual_payment = fields.Boolean(string="Is Manual Payment?", default=False)

    moneris_account_payment = fields.Many2one("account.payment",string="Moneris Account Payment" )

    moneris_refund_card_info = fields.Char(string="Moneris Payment Card info")

    @api.onchange('group_payment')
    def _onchange_group_payment(self):
        _logger.info("\n _onchange_group_payment")
        for rec in self:
            rec.moneris_move_name = ""
            if rec.group_payment == True and len(rec.line_ids.move_id) > 1:
                flag = False
                for line in rec.line_ids.move_id:
                    rec.moneris_move_name += line.name if flag == False else "," + line.name
                    flag = True

        _logger.info("\n--------------\n _onchange_group_payment: " + rec.moneris_move_name + "\n-----------")

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        for rec in self:
            rec.moneris_move_name = ""
            _logger.info("\n _onchange_journal_id")
            if rec.group_payment == False and len(rec.line_ids.move_id) == 1:
                rec.moneris_move_name = rec.line_ids.move_id.name
            if rec.group_payment == True and len(rec.line_ids.move_id) > 1:
                flag = False
                for line in rec.line_ids.move_id:
                    rec.moneris_move_name += line.name if flag == False else "," + line.name
                    flag = True

            _logger.info("\n--------------\n _onchange_group_payment: " + rec.moneris_move_name + "\n-----------")

            print("use_cloud_terminal ===>>>", rec.journal_id.use_cloud_terminal)
            print("payment_type ===>>>", rec.payment_type)
            print("payment_type_inbound ===>>>", rec.payment_type_inbound)
            print("payment_type_outbound ===>>>", rec.payment_type_outbound)

            rec.use_cloud_terminal = rec.support_mcloud_terminal = rec.payment_type_inbound = False
            if rec.journal_id and rec.journal_id.use_cloud_terminal:
                rec.use_cloud_terminal = True
                rec.support_mcloud_terminal = True
                # if rec.payment_method_code == 'electronic':
                #     rec.support_mcloud_terminal = True
                #     if rec.payment_type == 'inbound':
                #         rec.payment_type_inbound = True
                #     if rec.payment_type == 'outbound':
                #         rec.payment_type_outbound = True

            print("*******************AFTER************************************")
            print("payment_type_inbound ===>>>", rec.payment_type_inbound)
            print("payment_type_outbound ===>>>", rec.payment_type_outbound)
            print("------------------------------------------------------------")

    @api.onchange('journal_id')
    def _onchange_account_payment_options(self):
        self.ensure_one()
        try:
            if self.journal_id.use_cloud_terminal:

                if self.env.context.get("active_model") == "account.move" and self.payment_type == 'outbound':
                    active_move_id = self.env['account.move'].browse(self.env.context.get("active_ids"))
                    source_move_id = active_move_id.reversed_entry_id
                    payment_values = source_move_id._get_reconciled_info_JSON_values()
                    payment_ids = [i.get("account_payment_id") for i in payment_values]
                    print(payment_ids)
                    if payment_ids:
                        self.moneris_account_payment = payment_ids[0]
                    return {
                        'domain': {'moneris_account_payment': [('id', 'in', payment_ids),("is_moneris_refunded","=",False),("journal_id","=",self.journal_id.id)]},
                    }
            else:
                return {'domain': {'moneris_account_payment': [('id', '=', None)]}}
        except:
            pass



    @api.onchange('moneris_account_payment')
    def _onchange_moneris_account_payment(self):
        self.ensure_one()
        try:
            if self.journal_id.use_cloud_terminal and self.env.context.get(
                    "active_model") == "account.move" and self.payment_type == 'outbound':
                self.amount = self.moneris_account_payment.amount
                self.moneris_cloud_receiptid = self.moneris_account_payment.moneris_cloud_receiptid
                self.moneris_cloud_transid = self.moneris_account_payment.moneris_cloud_transid
                self.moneris_refund_card_info = (self.moneris_account_payment.moneris_cloud_cardname or "")+":" + (self.moneris_account_payment.moneris_cloud_pan[-4:] or "")

        except:
            pass


    moneris_cloud_receiptid = fields.Char(store=True)
    moneris_cloud_transid = fields.Char(store=True)

    # @api.onchange('journal_id')
    # def _compute_move_orderpay_moneris(self):
    #     for rec in self:
    #         if rec.journal_id.use_cloud_terminal == True and rec.payment_type == 'outbound':
    #             comm = rec.communication
    #             if comm:
    #                 inv_names = comm.split("Reversal of: ")
    #                 if len(inv_names) > 1:
    #                     inv_name = inv_names[1].split(",")[0]
    #                     _logger.info("inv_name--->" + inv_name)
    #                     AccPaymnt = self.env['account.payment']
    #                     pay_id = AccPaymnt.sudo().search(
    #                         [('move_id.ref', '=', inv_name)])
    #                     if pay_id:
    #                         rec.moneris_cloud_receiptid = pay_id.moneris_cloud_receiptid
    #                         rec.moneris_cloud_transid = pay_id.moneris_cloud_transid

    @api.onchange('amount')
    def _onchange_amount(self):
        _logger.info("\n_onchange_journal_amt")
        for rec in self:

            amount_residual_signed = sum(
                rec.line_ids.move_id.filtered(lambda r: r.state == "posted").mapped("amount_residual_signed"))
            _logger.info("\namount_residual_signed: %.2f, amount: %.2f" % (amount_residual_signed, rec.amount))

            if rec.journal_id and rec.journal_id.use_cloud_terminal == True and \
                    rec.payment_method_id.code == 'electronic':

                # Invoice Payment Check
                if rec.payment_type == 'inbound' and rec.amount > amount_residual_signed:
                    raise UserError(_("You can not pay with this amount." + \
                                      "\nPayment Amount: %s%s,\nInvoice Due: %s %s" % (
                                      rec.currency_id.symbol, "{:.2f}".format(rec.amount), rec.currency_id.symbol,
                                      "{:.2f}".format(amount_residual_signed))))
                # Credit Note Payment Check
                if rec.payment_type == 'outbound' and rec.amount > abs(amount_residual_signed):
                    raise UserError(_("You can not refund with this amount." + \
                                      "\nPayment Amount: %s - %s,\nCredit Note Due Amount: %s %s" % (
                                      rec.currency_id.symbol, "{:.2f}".format(rec.amount), rec.currency_id.symbol,
                                      "{:.2f}".format(amount_residual_signed))))

    def _send_moneris_request(self, values):
        srm = AppPayment(service_name='moneris_cloud', service_type=values.get("service_type"),
                         service_key=values.get("token"))
        srm.data = values.get("data")
        # if service_type == "refund":
        #     srm.data.update({
        #         "txn_number": datas.get('txnNumber')
        #     })

        response = srm.payment_process(company_id=self.company_id.id)

        # response = {
        #     "receipt":
        #         {"Completed": "true",
        #          "TransType": "00",
        #          "Error": "false",
        #          "InitRequired": "false",
        #          "SafIndicator": "N",
        #          "ResponseCode": "027",
        #          "ISO": "01",
        #          "LanguageCode": "5",
        #          "PartialAuthAmount": None,
        #          "AvailableBalance": None,
        #          "TipAmount": None,
        #          "EMVCashBackAmount": None,
        #          "SurchargeAmount": None,
        #          "ForeignCurrencyAmount": None,
        #          "ForeignCurrencyCode": None,
        #          "BaseRate": None,
        #          "ExchangeRate": None,
        #          "Pan": "************4111",
        #          "CardType": "M ",
        #          "CardName": "MASTERCARD",
        #          "AccountType": "4",
        #          "SwipeIndicator": "C",
        #          "FormFactor": None,
        #          "CvmIndicator": "P",
        #          "ReservedField1": None,
        #          "ReservedField2": None,
        #          "AuthCode": "863602",
        #          "InvoiceNumber": None,
        #          "EMVEchoData": None,
        #          "ReservedField3": None,
        #          "ReservedField4": None,
        #          "Aid": "A0000000041010",
        #          "AppLabel": "MASTERCARD",
        #          "AppPreferredName": "MasterCard",
        #          "Arqc": "A81BD7A3A2030B43",
        #          "TvrArqc": "0400008000",
        #          "Tcacc": "58DA77EFCDE114DB",
        #          "TvrTcacc": "0400008000",
        #          "Tsi": "E800",
        #          "TokenResponseCode": "00",
        #          "Token": None,
        #          "LogonRequired": "N",
        #          "EncryptedCardInfo": None,
        #          "TransDate": "21-12-23",
        #          "TransTime": "09:11:06",
        #          "Amount": 1000,
        #          "ReferenceNumber": "P15031060010010090",
        #          "ReceiptId": "Order 00007-001-0001/1",
        #          "TransId": "505-0_20",
        #          "TimedOut": "false",
        #          "CloudTicket": "bf540469-34f5-45f6-9600-141db6fed05d",
        #          "TxnName": "Purchase" } }

        _logger.info("moneris_validation response-->")
        _logger.info(response)
        # _logger.info(req)
        # _logger.info(req.text)
        # if req.status_code != 200:
        if response.get("error"):
            response = {"error": True, "description": response.get("error")}
        elif response.get('errors_message'):
            response = {"error": True, "description": response.get('errors_message')}
        return response


    def check_error_conditions(self):

        if not self.moneris_cloud_receiptid and not self.moneris_cloud_transid:
            raise UserError(_("No associate Payment Found!!"))

    def _create_payments(self):
        if self.journal_id.use_cloud_terminal and self.payment_type =="outbound":
            self.check_error_conditions()
        return super(AccountPaymentRegister, self)._create_payments()
            
        
    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        try:
            journal = request.env['account.journal'].search(
                [('id', '=', res.get("journal_id"))])
            if journal.use_cloud_terminal:

                omni_sync_token = journal.token
                if res.get("payment_type") == "inbound":

                    moneris_val = {
                        "data": {
                            "order_id": res.get("ref"),
                            "amount": str(round(res.get("amount"), 2)),
                            "is_manual": self.moneris_is_manual_payment
                        },
                        "service_type": "purchase",
                        "token": omni_sync_token
                    }
                elif res.get("payment_type") == "outbound":
                    self.check_error_conditions()
                    moneris_val = {
                        "data": {
                            "order_id": self.moneris_cloud_receiptid,
                            "amount": str(round(res.get("amount"), 2)),
                            "txn_number": self.moneris_cloud_transid,
                            "is_manual": self.moneris_is_manual_payment
                        },
                        "service_type": "refund",
                        "token": omni_sync_token,

                    }
                data = self._send_moneris_request(values=moneris_val)
                if data.get("error") != True:
                    response = data.get("receipt")
                    if response.get('Error') == 'false' and (
                            response.get('ResponseCode') and int(response.get('ResponseCode')) < 50):
                        res.update({
                            "moneris_cloud_completed": response.get('Completed'),
                            "moneris_cloud_transtype": response.get('TransType'),
                            "moneris_cloud_error": response.get('Error'),
                            "moneris_cloud_initrequired": response.get('InitRequired'),
                            "moneris_cloud_safindicator": response.get('SafIndicator'),
                            "moneris_cloud_responsecode": response.get('ResponseCode'),
                            "moneris_cloud_iso": response.get('ISO'),
                            "moneris_cloud_languagecode": response.get('LanguageCode'),
                            "moneris_cloud_partailauthamount": response.get('PartialAuthAmount'),
                            "moneris_cloud_availablebalance": response.get('AvailableBalance'),
                            "moneris_cloud_tipamount": response.get('TipAmount'),
                            "moneris_cloud_emvcashbackamount": response.get('EMVCashBackAmount'),
                            "moneris_cloud_surchargeamount": response.get('SurchargeAmount'),
                            "moneris_cloud_foreigncurrencyamount": response.get('ForeignCurrencyAmount'),
                            "moneris_cloud_baserate": response.get('BaseRate'),
                            "moneris_cloud_exchangerate": response.get('ExchangeRate'),
                            "moneris_cloud_pan": response.get('Pan'),
                            "moneris_cloud_cardtype": response.get('CardType'),
                            "moneris_cloud_cardname": response.get('CardName'),
                            "moneris_cloud_accounttype": response.get('AccountType'),
                            "moneris_cloud_swipeindicator": response.get('SwipeIndicator'),
                            "moneris_cloud_formfactor": response.get('FormFactor'),

                            "moneris_cloud_cvmindicator": response.get('CvmIndicator'),
                            "moneris_cloud_reservedfield1": response.get('ReservedField1'),
                            "moneris_cloud_reservedfield2": response.get('ReservedField2'),
                            "moneris_cloud_authcode": response.get('AuthCode'),
                            "moneris_cloud_invoicenumber": response.get('InvoiceNumber'),
                            "moneris_cloud_emvechodata": response.get('EMVEchoData'),
                            "moneris_cloud_reservedfield3": response.get('ReservedField3'),
                            "moneris_cloud_reservedfield4": response.get('ReservedField4'),
                            "moneris_cloud_aid": response.get('Aid'),
                            "moneris_cloud_applabel": response.get('AppLabel'),
                            "moneris_cloud_apppreferredname": response.get('AppPreferredName'),
                            "moneris_cloud_arqc": response.get('Arqc'),
                            "moneris_cloud_tvrarqc": response.get('TvrArqc'),
                            "moneris_cloud_tcacc": response.get('Tcacc'),
                            "moneris_cloud_tvrtcacc": response.get('TvrTcacc'),
                            "moneris_cloud_tsi": response.get('Tsi'),
                            "moneris_cloud_tokenresponsecode": response.get('TokenResponseCode'),
                            "moneris_cloud_token": response.get('Token'),
                            "moneris_cloud_logonrequired": response.get('LogonRequired'),
                            "moneris_cloud_cncryptedcardinfo": response.get('EncryptedCardInfo'),
                            "moneris_cloud_transdate": response.get('TransDate'),
                            "moneris_cloud_transtime": response.get('TransTime'),
                            "moneris_cloud_amount": response.get('Amount'),
                            "moneris_cloud_referencenumber": response.get('ReferenceNumber'),
                            "moneris_cloud_receiptid": response.get('ReceiptId'),
                            "moneris_cloud_transid": response.get('TransId'),
                            "moneris_cloud_timeout": response.get('TimedOut'),
                            "moneris_cloud_cloudticket": response.get('CloudTicket'),
                            "moneris_cloud_txnname": response.get('TxnName')
                        })
                        # ======= Refund =============
                        if res.get("payment_type") == "outbound":
                            self.moneris_account_payment.is_moneris_refunded = True

                        return res
                    else:
                        if response.get('ResponseCode') and int(response.get('ResponseCode')) > 50:
                            raise Exception("Payment Declined!")
                        else:
                            if response.get("ErrorCode"):
                                raise Exception(f"Payment Declined!")
                            raise Exception("Payment Incomplete!")
                else:
                    raise Exception(data.get("description"))
            else:
                return res


        except Exception as e:
            raise UserError(_(e))

    # @api.model
    # def action_create_payments(self, vals=None):
    #     _logger.info("action_create_payments----------------->")
    #     """Override account.payment.registe>>action_create_payments method
    #        This function writes moneris details on the account.payment record
    #     """
    #     res=

    #
    # record = self.browse(vals) if len(self) == 0 else self
    #
    # payments = record._create_payments()
    #
    # # ----------------------------------------------------------
    # if len(payments) > 0:
    #     _logger.info("payments-->" +str(payments))
    #     record._update_moneris_cloud_values(payments, record.env.context)
    #     # TO DO: Flush or Remove the Context
    #     try:
    #         context = record.env.context.copy()
    #         _logger.info("context ===>>>")
    #         context.update({'terminalResponse': False})
    #         record.env.context = context
    #     except Exception as e:
    #         _logger.info("Exception ===>>>" + str(e.args))
    #     try:
    #         context = request.env.context.copy()
    #         _logger.info("context ===>>>")
    #         context.update({'terminalResponse': False})
    #         request.env.context = context
    #     except Exception as e:
    #         _logger.info("Exception ===>>>" + str(e.args))
    #
    #
    # # ----------------------------------------------------------
    #
    # if record._context.get('dont_redirect_to_payments'):
    #     return True
    #
    # action = {
    #     'name': _('Payments'),
    #     'type': 'ir.actions.act_window',
    #     'res_model': 'account.payment',
    #     'context': {'create': False},
    # }
    # if len(payments) == 1:
    #     action.update({
    #         'view_mode': 'form',
    #         'res_id': payments.id,
    #     })
    # else:
    #     action.update({
    #         'view_mode': 'tree,form',
    #         'domain': [('id', 'in', payments.ids)],
    #     })
    # return action

    def _update_moneris_cloud_values(self, payments, context):
        """Function to update Moneris Cloud Values

        Args:
            payments ([dict]): Dict of Payment Values
            context (context): Request Context Values
        """
        if self.journal_id.use_cloud_terminal:
            if self.group_payment == True and len(self.line_ids.move_id) > 1:
                move_name = self.moneris_move_name or payments.ref

            if len(self.line_ids.move_id) == 1:
                move_name = self.moneris_move_name or payments.ref
                move_name = move_name.split(": ")[1] if ": " in move_name else move_name
                move_name = move_name.split(",")[0] if "," in move_name else move_name

            if context.get('terminalResponse'):

                _logger.info('\nTerminal Response\n' +
                             str(context.get('terminalResponse')))

                if len(payments) == 1:
                    tranRes = context.get('terminalResponse')
                    tranRes = json.loads(tranRes)

                    active_id = context.get('active_id') or context.get('active_ids')
                    accMove = request.env['account.move'].sudo().search(
                        [('id', '=', active_id)])

                    if len(accMove) > 0:
                        _logger.info("accMove ===>>> " + str(accMove) +
                                     "\n moneris_last_action ===>>> " + str(accMove[0].moneris_last_action))

                        action = 'PURCHASE'
                        if accMove[0].moneris_last_action == 'PURCHASE':
                            action = 'PURCHASE'
                        if accMove[0].moneris_last_action == 'REFUND':
                            action = 'REFUND'

                        # Response Different for Moneris Cloud
                        receipt = tranRes.get("receipt", {})
                        Completed = receipt.get("Completed")
                        card = receipt.get("card_type")

                        paidamt = payments.amount

                        if action == "REFUND" or action == "PURCHASE":
                            ter_amt = str(receipt.get("Amount"))

                        _logger.info(
                            "\n action--->" + str(action) +
                            "\n paidamt--->" + str(paidamt) +
                            "\n ter_amt--->" + str(ter_amt) +
                            "\n payments.ref--->" + str(payments.ref) +
                            "\n invoice_origin--->" + str(payments.invoice_origin) +
                            "\n invoice_name--->" + str(payments.move_id.name) +
                            "\n move_name--->" + str(move_name) +
                            "\n moneris_move_name--->" + str(self.moneris_move_name)
                        )

                        if payments.journal_id.use_cloud_terminal == True:
                            _logger.info(
                                "use_cloud_terminal--->" + str(payments.journal_id.use_cloud_terminal))
                            if paidamt == ter_amt:
                                _logger.info("Amount Matches")
                            if move_name != False:
                                if move_name in receipt.get('TransId'):
                                    _logger.info("transactionId Matches")

                            amt_tran = False
                            if paidamt == ter_amt and move_name in receipt.get('TransId'):
                                amt_tran = True

                            if len(self.line_ids.move_id) == 1:
                                if paidamt == ter_amt and \
                                        self.line_ids.move_id.display_name.split(" ")[0] in receipt.get('TransId'):
                                    amt_tran = True

                            if len(self.line_ids.move_id) > 1 and paidamt == ter_amt:
                                for move_id in self.line_ids.move_id:
                                    amt_tran = True if move_id.name in receipt.get('TransId') else False
                            print(amt_tran)
                            # ===========================
                            amt_tran = True
                            # ===========================
                            if amt_tran == True:
                                _logger.info("Amount and transactionId Matches")
                                # NEED TO CHECK VALUES
                                payment_vals = {
                                    'moneris_cloud_cloudticket': receipt.get('CloudTicket'),
                                    'moneris_cloud_receiptid': receipt.get('ReceiptId'),  # Important for REFUND
                                    'moneris_cloud_transid': receipt.get('TransId'),  # Important for REFUND
                                    'moneris_cloud_completed': receipt.get('Completed'),
                                    'moneris_cloud_transtype': receipt.get('TransType'),
                                    'moneris_cloud_error': receipt.get('Error'),
                                    'moneris_cloud_responsecode': receipt.get('ResponseCode'),
                                    'moneris_cloud_iso': receipt.get('ISO'),
                                    'moneris_cloud_pan': receipt.get('Pan'),
                                    'moneris_cloud_cardtype': receipt.get('CardType'),
                                    'moneris_cloud_accounttype': receipt.get('AccountType'),
                                    'moneris_cloud_cvmindicator': receipt.get('CvmIndicator'),
                                    'moneris_cloud_authcode': receipt.get('AuthCode'),
                                    'moneris_cloud_timeout': receipt.get('TimedOut'),
                                    'moneris_cloud_txnname': receipt.get('TxnName'),
                                    'moneris_cloud_transdate': receipt.get('TransDate'),
                                    'moneris_cloud_transtime': receipt.get('TransTime'),
                                }
                                if receipt.get('moneris_cloud_transtype') == 'Purchase':
                                    payment_vals['purchase_receipt_id'] = receipt.get('ReceiptId')
                                print(payment_vals)

                                payments.write(payment_vals)
