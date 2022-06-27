###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import datetime
import json
import logging
from math import ceil

import requests
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.service import common

version_info = common.exp_version()
server_serie = version_info.get("server_serie")

_logger = logging.getLogger(__name__)
BATCH_API = "https://api.na.bambora.com/v1/batchpayments"
REPORT_API = "https://api.na.bambora.com/scripts/reporting/report.aspx"

#pylint: disable=logging-not-lazy


class BatchPaymentTracking(models.Model):
    _name = "batch.payment.tracking"
    _description = "Bambora Batch Payment Tracking"
    _rec_name = "batch_id"

    transaction_date = fields.Date("Payment Date")
    transaction_id = fields.Integer("Transaction ID")
    invoice_no = fields.Many2one("account.move", "Invoice Number")
    invoice_ref = fields.Char("Reference")
    invoice_partner_id = fields.Many2one("res.partner", "Partner")
    invoice_partner_bank_id = fields.Many2one("res.partner.bank", "Bank Account Number")
    invoice_date = fields.Date("Invoice Date")
    settlement_date = fields.Date("Settlement Date")
    batch_id = fields.Char("Batch ID")
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_process", "In process"),
            ("rejected", "Rejected"),
            ("complete", "Complete"),
            ("duplicate", "Duplicate"),
        ],
        "Transaction State",
        default="scheduled",
    )
    status = fields.Char("Status Name")
    remain_settle_day = fields.Char("Remaining days to Settle")

    # Sale Order
    sale_ok = fields.Boolean(
        string="Sale Batch?",
    )
    transaction_ids = fields.One2many(
        string="Transaction Ids",
        comodel_name="payment.transaction",
        inverse_name="batch_track_id",
    )
    acquirer_id = fields.Many2one("payment.acquirer", "Acquirer")

    def _create_payment_vals(self, move_id, acquirers):
        pay_mthd = self.env["account.payment.method"].sudo()
        if move_id.type == "out_invoice":
            payment_type = "inbound"
            partner_type = "customer"
            journal_id = acquirers.journal_id.id
            payment_method_id = pay_mthd.sudo().search(
                [
                    ("code", "=", "electronic"),
                    ("payment_type", "=", payment_type),
                ],
                limit=1,
            )
        if move_id.type == "in_invoice":
            payment_type = "outbound"
            partner_type = "supplier"
            journal_id = acquirers.bamboraeft_vendor_journal_id.id
            payment_method_id = pay_mthd.sudo().search(
                [
                    ("code", "=", "manual"),
                    ("payment_type", "=", payment_type),
                ],
                limit=1,
            )
        payment_vals = {
            "payment_date": datetime.date.today(),
            "amount": move_id.amount_total,
            "payment_type": payment_type,
            "partner_type": partner_type,
            # 'ref': move_id.name,
            "journal_id": journal_id,
            # 'currency_id': move_id.journal_id.currency_id.id,
            "partner_id": move_id.partner_id.id,
            "partner_bank_account_id": move_id.invoice_partner_bank_id.id,
            "payment_method_id": payment_method_id.id,
            # 'destination_account_id': 4,  # ===>>>Need to change from 4
            "payment_token_id": False,
            # 'invoice_origin': move_id.invoice_origin,
            # 'move_id' : move_id.id,
            # 'type': 'out_invoice',
            "state": "draft",
            "payment_reference": move_id.name,
            # 'is_reconciled': True/False,
            # 'is_matched' : True/False,
        }
        return payment_vals

    def _cron_check(self, cron_interval):
        cron_settings = self.env["bambora.cron.settings"].search([], limit=1, order="cron_datetime desc")
        is_batch_id = False

        if not cron_settings:
            cron_settings = self.env["bambora.cron.settings"].create(
                {
                    "transaction_start": 0,
                    "transaction_end": 0,
                    "cron_datetime": datetime.datetime.now(),
                }
            )

        batch_rec = self.env["batch.payment.tracking"]
        batch_data = batch_rec.search(
            [
                ("state", "not in", ("complete", "rejected")),
                ("transaction_id", "!=", 0),
            ]
        )
        transaction_data = batch_data.mapped("transaction_id")

        if transaction_data:
            min_trasaction = min(transaction_data)
            max_trasaction = max(transaction_data)
            if cron_settings.transaction_start == 0:
                start = min_trasaction
                end = start + cron_interval
            else:
                start = cron_settings.transaction_start
                end = start + cron_interval

            if end > max_trasaction:
                end = max_trasaction
            self.env["bambora.cron.settings"].create(
                {
                    "transaction_start": end,
                    "transaction_end": end + cron_interval,
                    "cron_datetime": datetime.datetime.now(),
                }
            )
        else:
            batch_data = batch_rec.search(
                [
                    ("state", "not in", ("complete", "rejected"))
                ]
            )
            batch_id_data = batch_data.mapped("batch_id")
            is_batch_id = True if batch_id_data else False
            start = int(min(batch_id_data)) if is_batch_id else 1
            end = int(max(batch_id_data)) if is_batch_id else 2
            min_trasaction = 1
            max_trasaction = 1

        return start, end, max_trasaction, min_trasaction,is_batch_id

    def _batch_data_update(self, response_dict, acquirers):
        if response_dict["response"]["code"] == 1:
            if response_dict["response"]["records"] != '':
                records = response_dict["response"]["record"]
                for data in records:
                    rec = self.env["batch.payment.tracking"].search(
                        [
                            ("invoice_no", "=", data["reference"]),
                            ("batch_id", "=", data["batchId"]),
                        ],
                        limit=1,
                    )

                    ################################################
                    #Vendor Bill Testing
                    if data["batchId"] in [	10000032]:
                        data["stateName"] = "Complete"
                    ################################################

                    if rec and not rec.state == "complete":
                        sett_date = datetime.datetime.strptime(data["settlementDate"], "%Y-%m-%d")
                        date_today = datetime.datetime.today()

                        difference = (sett_date - date_today).days
                        _logger.info(difference)

                        if data["stateName"] == "Complete":
                            self.update_bamboraeft_inv(data, acquirers)

                        if data["stateName"] == "In Process":
                            state = "in_process"
                        elif data["stateName"] == "Duplicate Batch":
                            state = "duplicate"
                        else:
                            state = data["stateName"].lower()
                        rec.update(
                            {
                                "transaction_id": data["transId"],
                                "state": state,
                                "status": data["statusName"],
                                "settlement_date": sett_date,
                                "remain_settle_day": difference,
                            }
                        )

                    self.update_bamboraeft_tx(data)
            else:
                _logger.warning(_("No data found on bambora batch payment."))

        else:
            raise AccessError(_(response_dict["response"]["message"]))

        _logger.info("------ Batch API update done -----")

    def action_report_bamboraeft_batch_payment(self):
        domain = [("provider", "=", "bamboraeft")]
        domain += [("state", "!=", "disabled")]
        acquirers = self.env["payment.acquirer"].sudo().search(domain)
        for rec_aq in acquirers:
            pass_code = acquirers.bamboraeft_report_api
            header = {"content-type": "application/xml"}
            service_name = "BatchPaymentsEFT" if acquirers.bamboraeft_transaction_type == "E" else "BatchPaymentsACH"
            rpt_version = rec_aq.bamboraeft_report_api_version
            merchant_id = rec_aq.bamboraeft_merchant_id
            cron_interval = rec_aq.bambora_record_interval
            # current_datetime = datetime.datetime.today()
            # previous_datetime = (current_datetime - datetime.timedelta(days=20)).replace(hour=00, minute=00, second=1)

            # -------------------- Cron Handle Part--------------------------------
            start, end, max_trasaction, min_trasaction,is_batch_id = self._cron_check(cron_interval)

            # -------------------- X Cron Handle Part X--------------------------------

            if is_batch_id:
                data = """<?xml version="1.0" encoding="utf-8"?><request><rptVersion>%s</rptVersion><serviceName>%s</serviceName><merchantId>%s</merchantId><passCode>%s</passCode><sessionSource>external</sessionSource><rptFormat>JSON</rptFormat><rptFilterBy1>batch_id</rptFilterBy1><rptOperationType1>GE</rptOperationType1><rptFilterValue1>%s</rptFilterValue1><rptAddCondition1>AND</rptAddCondition1><rptFilterBy2>batch_id</rptFilterBy2><rptOperationType2>LE</rptOperationType2><rptFilterValue2>%s</rptFilterValue2></request>""" % (
                    rpt_version,
                    service_name,
                    merchant_id,
                    pass_code,
                    start,
                    end,
                )
            else:

                data = """<?xml version="1.0" encoding="utf-8"?><request><rptVersion>%s</rptVersion><serviceName>%s</serviceName><merchantId>%s</merchantId><passCode>%s</passCode><sessionSource>external</sessionSource><rptFormat>JSON</rptFormat><rptFilterBy1>trans_id</rptFilterBy1><rptOperationType1>GE</rptOperationType1><rptFilterValue1>%s</rptFilterValue1><rptAddCondition1>AND</rptAddCondition1><rptFilterBy2>trans_id</rptFilterBy2><rptOperationType2>LE</rptOperationType2><rptFilterValue2>%s</rptFilterValue2><rptAddCondition2>OR</rptAddCondition2><rptFilterBy3>trans_id</rptFilterBy3><rptOperationType3>GT</rptOperationType3><rptFilterValue3>%s</rptFilterValue3><rptAddCondition3>AND</rptAddCondition3><rptFilterBy4>trans_id</rptFilterBy4><rptOperationType4>LE</rptOperationType4><rptFilterValue4>%s</rptFilterValue4></request>""" % (
                    rpt_version,
                    service_name,
                    merchant_id,
                    pass_code,
                    start,
                    end,
                    max_trasaction,
                    max_trasaction + cron_interval,
                )
            _logger.info(data)

            try:
                response = requests.post(REPORT_API, headers=header, data=data)
                response_dict = json.loads(response.text)

                if rec_aq.debug_logging:
                    _logger.info("headers===>>>>" + str(header))
                    _logger.info("data ===>>>> " + str(data))
                    _logger.info("response ===>>>> " + str(response.status_code))
                    _logger.info("response_dict ===>>>> " + str(response_dict))

                self._batch_data_update(response_dict, acquirers)

                if end >= max_trasaction:
                    cron_settings = self.env["bambora.cron.settings"].create(
                        {
                            "transaction_start": 0,
                            "transaction_end": 0,
                            "cron_datetime": datetime.datetime.now(),
                        }
                    )
            except Exception as e:
                raise AccessError(_('Internal Problem . Please Try again!!. \n Error: {}'.format(e.args)))

    def update_bamboraeft_tx(self, data):
        pay_trx = self.env["payment.transaction"].sudo()
        self.update_salebatch_tracking(data)

        if data.get("reference"):
            if data.get("stateName") == "Complete":
                tx = pay_trx.search([("reference", "=", data["reference"])], limit=1)
                if tx.bamboraeft_batch_id.batch_id == str(data.get("batchId")) and float(tx.amount * 100) == float(
                    data.get("amount")
                ):
                    if tx.state == "pending" and float(tx.amount * 100) == float(data.get("amount")):
                        #############################################################################
                        tx._set_transaction_done()
                        #############################################################################
                    if tx.state == "done" and data.get("stateName") == "Complete":
                        if len(tx.sale_order_ids) > 0 and len(tx.invoice_ids) == 0:
                            order_ref = data.get("reference").split("-")[0]
                            if order_ref in tx.sale_order_ids[0].name:
                                if tx.sale_order_ids[0].state == "pending":
                                    tx.sale_order_ids[0].action_confirm()

                                _logger.info(
                                    "Payment Transaction-%s, Order-%s is successfully updated"
                                    % (str(tx), str(tx.sale_order_ids))
                                )
                                #####################################################################
                                ICPSudo = self.env['ir.config_parameter'].sudo()
                                automatic_invoice = ICPSudo.get_param('sale.automatic_invoice')
                                group_auto_done = ICPSudo.get_param('sale.group_auto_done_setting')
                                _logger.info("automatic_invoice ===>>> %s", automatic_invoice)
                                _logger.info("group_auto_done ===>>>%s", group_auto_done)
                                #Create Invoice if automatic_invoice is enabled
                                if automatic_invoice:
                                    tx._reconcile_after_transaction_done()
                                if group_auto_done and tx.sale_order_ids[0].state != "done":
                                    tx.sale_order_ids[0].action_done()
                                #####################################################################
 

                        if len(tx.invoice_ids) == 1 or len(tx.payment_id.invoice_ids) == 1:
                            move_id = tx.invoice_ids if len(tx.invoice_ids) == 1 else tx.payment_id.invoice_ids
                            if float(tx.amount * 100) == float(data.get("amount")):
                                inv_ref = data.get("reference").split("-")[0]
                                acc_move = self.env["account.move"].sudo()
                                move_id = acc_move.search([("name", "=", inv_ref)], limit=1)
                                if move_id and move_id.state != "paid":
                                    move_id.write({"invoice_payment_state": "paid"})


                                _logger.info(
                                    "Payment Transaction-%s, Order-%s is successfully updated"
                                    % (str(tx), str(tx.sale_order_ids))
                                )

                                if move_id.state == "posted":
                                    pay_id = tx.payment_id
                                    if not pay_id:
                                        acc_pay = self.env["account.payment"].sudo()
                                        pay_id = acc_pay.search(
                                            [
                                                ("amount", "=", move_id.amount_total),
                                                ("payment_reference", "=", move_id.name),
                                            ],
                                            limit=1,
                                        )
                                        if len(pay_id) == 0:
                                            payment_vals = self._create_payment_vals(move_id, tx.acquirer_id)
                                            pay_id = acc_pay.create(payment_vals)

                                        if len(pay_id) == 1:
                                            pay_id.write(
                                                {"payment_reference": move_id.name}
                                            ) if not pay_id.payment_reference else None

                                    if pay_id and pay_id.state in ["draft", "cancel"]:
                                        pay_id.action_post() if server_serie == "14.0" else pay_id.post()

                                    if pay_id and pay_id.state == "posted":
                                        ##########################################################################################
                                        if move_id.invoice_payment_state not in ["in_payment", "paid"]:
                                            move_id.write(
                                                {
                                                    "payment_id": pay_id.id,
                                                    "payment_reference": tx.reference,
                                                    "bambora_batch_payment_id": tx.bamboraeft_batch_id,
                                                }
                                            )
                                        if not pay_id.is_reconciled:
                                            pay_id.write({"is_reconciled": True})
                                        ##########################################################################################

                        if len(tx.invoice_ids) > 1:
                            """Handle multile Invoice Payment Transactions"""

            elif data.get("stateName") == "Rejected/Declined" or data.get("statusId") == 2:
                track_id = self.env["batch.payment.tracking"].sudo().search([("batch_id", "=", data.get("batchId"))])
                if track_id:
                    if track_id and track_id.transaction_id != data.get("transId"):
                        sett_date = datetime.datetime.strptime(data["settlementDate"], "%Y-%m-%d")
                        date_today = datetime.datetime.today()
                        difference = (sett_date - date_today).days
                        track_id.write(
                            {
                                "transaction_id": data.get("transId"),
                                "settlement_date": data.get("settlementDate"),
                                "state": data.get("stateName").lower(),
                                "status": data.get("statusName"),
                                "remain_settle_day": difference,
                            }
                        )

                if "RINV" in data.get("reference"):
                    move_id = self.env["account.move"].sudo().search([("name", "=", data.get("reference"))], limit=1)
                    if move_id.invoice_payment_state in ["paid", "in_payment"]:
                        move_id.write({"invoice_payment_state": "not_paid"})
                    tx = self.env["payment.transaction"].sudo().search([("reference", "=", move_id.ref)])

                    if tx and tx.payment_id:
                        if tx.state != "cancel":
                            tx.write({"state": "cancel"})
                        if tx.payment_id.state != "cancel":
                            tx.payment_id.write({"state": "cancel"})

                if "RBILL" in data.get("reference"):
                    move_id = self.env["account.move"].sudo().search([("name", "=", data.get("reference"))], limit=1)
                    if move_id.invoice_payment_state in ["paid", "in_payment"]:
                        move_id.write({"invoice_payment_state": "not_paid"})
                    tx = self.env["payment.transaction"].sudo().search([("reference", "=", move_id.ref)])

                    if tx and tx.payment_id:
                        if tx.state != "cancel":
                            tx.write({"state": "cancel"})
                            tx.payment_id.write({"state": "cancel"})

    def update_salebatch_tracking(self, data):
        """Update Sale Order Batch Payment Tracking

        Args:
            data ([dict]): [A dict containing bambora batch transaction record]
        """
        domain = [("invoice_ref", "=", data["reference"])]
        domain += [("acquirer_id.provider", "=", "bamboraeft")]
        domain += [("sale_ok", "=", True)]
        rec = self.env["batch.payment.tracking"].search(domain, limit=1)
        if rec and not rec.state == "complete":
            sett_date = datetime.datetime.strptime(data["settlementDate"], "%Y-%m-%d")
            date_today = datetime.datetime.today()
            difference = (sett_date - date_today).days
            if data["stateName"] == "In Process":
                state = "in_process"
            elif data["stateName"] == "Duplicate Batch":
                state = "duplicate"
            else:
                state = data["stateName"].lower()
            rec.update(
                {
                    "transaction_id": data["transId"],
                    "state": state,
                    "status": data["statusName"],
                    "settlement_date": sett_date,
                    "remain_settle_day": difference,
                }
            )

    def update_bamboraeft_inv(self, data, acquirers):
        move_id = self.env["account.move"].search([("name", "=", data["reference"])], limit=1)
        if server_serie == "13.0":
            if not move_id.invoice_origin and move_id.invoice_payment_state == "not_paid":
                if move_id.state == "posted":
                    register_payment_wizard = self.env['account.payment.register'].with_context(
                        active_model='account.move',
                        active_ids=[move_id.id]).create({
                        'journal_id': self.env.ref('bambora_batch_payment.bamboraeft_customer_journal').id,
                        'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id
                    })
                    register_payment_wizard.create_payments()
                    # pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.invoice', active_ids=caba_inv.ids).create({
                    #     'payment_date': caba_inv.date,
                    #     'journal_id': self.bank_journal_euro.id,
                    #     'payment_method_id': self.inbound_payment_method.id,
                    # })
                    # pmt_wizard.create_payments()
                    _logger.info("------ Invoice Payment Success -----")


        if server_serie == "14.0":
            if not move_id.invoice_origin and move_id.payment_state == "not_paid":
                if move_id.state == "posted":
                    register_payment_wizard = self.env['account.payment.register'].with_context(
                        active_model='account.move',
                        active_ids=[move_id.id]).create({
                        'journal_id': self.env.ref('bambora_batch_payment.bamboraeft_customer_journal').id,
                        'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id
                    })
                    register_payment_wizard._create_payments()
                    _logger.info("------ Invoice Payment Success -----")

    def batch_payment_cron_check_status(self):
        """check_status"""

        domain = [("provider", "=", "bamboraeft")]
        domain += [("state", "!=", "disabled")]
        acquirers = self.env["payment.acquirer"].sudo().search(domain, limit=1)
        if acquirers:
            batch_rec = self.env["batch.payment.tracking"]
            batch_data = batch_rec.search(
                [
                    ("state", "not in", ("complete", "rejected")),
                    ("transaction_id", "!=", ""),
                ]
            )
            transaction_data_count = len(batch_data.mapped("transaction_id"))

            ir_cron_bambora_report = self.env.ref("bambora_batch_payment.ir_cron_fetch_report_bamboraeft_batch")

            minimum_cron_need = ceil(transaction_data_count / acquirers.bambora_record_interval)

            if ir_cron_bambora_report:
                cron_interval_number = ir_cron_bambora_report.interval_number
                cron_interval_type = ir_cron_bambora_report.interval_type
                if cron_interval_type == "days":
                    cron_interval_number_min = 24 * 60
                elif cron_interval_type == "hours":
                    cron_interval_number_min = cron_interval_number * 60
                else:
                    cron_interval_number_min = cron_interval_number

                current_cron = 1440 / cron_interval_number_min

                if minimum_cron_need > current_cron:
                    template = self.env.ref("bambora_batch_payment.email_template")
                    partners_ids = [(4, p.id) for p in acquirers.partner_ids]

                    force_vals = {
                        # 'email_to': acquirers.partner_ids[0].email,
                        # 'email_from': '',#self.env.user.partner_id.email,
                        "minimum_cron_need": minimum_cron_need,
                        "current_cron": current_cron,
                    }
                    template.with_context(force_vals).send_mail(
                        self.id,
                        force_send=True,
                        raise_exception=False,
                        email_values={"recipient_ids": partners_ids},
                    )

            else:
                MissingError(_("No report cron created . Please check or reinstall ."))
        else:
            UserError(_("Module not install or disable."))


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    batch_track_id = fields.Many2one(
        string="Batch Track",
        comodel_name="batch.payment.tracking",
        ondelete="restrict",
    )


class BamboraSettings(models.Model):
    _name = "bambora.cron.settings"
    _description = "Bambora Cron Settings"

    transaction_start = fields.Integer("Bambora Cron Starting Transaction")
    transaction_end = fields.Integer("Bambora Cron End Transaction")
    cron_datetime = fields.Datetime("Cron Date Time")


class InheritIrCron(models.Model):
    _inherit = "ir.cron"

    @api.onchange("interval_number", "interval_type")
    def _check_auto_exclusion(self):
        if self.xml_id == "bambora_batch_payment.ir_cron_fetch_report_bamboraeft_batch_ir_actions_server":
            if self.interval_type in ["weeks", "months"]:
                UserError(_("Bambora EFT Report Cron must be set minute or hours or in 1 days!"))
            elif self.interval_type == "days":
                if self.interval_number > 1:
                    UserError(_("Bambora EFT Report Cron must be set minimum 1 days!"))
