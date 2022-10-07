###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################
#pylint: disable=logging-not-lazy

import base64
import json
import logging
import pprint
import random
import string

import requests
from odoo import _, api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.service import common

_logger = logging.getLogger(__name__)
version_info = common.exp_version()
server_serie = version_info.get("server_serie")

BATCH_API = "https://api.na.bambora.com/v1/batchpayments"
REPORT_API = "https://api.na.bambora.com/scripts/reporting/report.aspx"
PROFILE_URL = "https://api.na.bambora.com/v1/profiles"

BAMBORAEFT_COUNTRY_TYPE = [
    ('canadian', 'Canadian'),
    ('american', 'American')
]
BANK_ACCOUNT_TYPE = [
    ('PC', 'Personal Checking'),
    ('PS', 'Personal Savings'),
    ('CC', 'Corporate Checking'),
    ('CS', 'Corporate Savings'),
]

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def get_authorization(merchant_id, api_key):
    message = merchant_id + ":" + api_key
    base64_bytes = base64.b64encode(message.encode("ascii"))
    base64_message = base64_bytes.decode("ascii")
    return base64_message


def get_headers(merchant_id, api_key):
    headers = {
        "Authorization": "Passcode " + get_authorization(merchant_id, api_key),
        "Content-Type": "application/json",
    }
    return headers


class ResPartner(models.Model):
    _inherit = "res.partner"

    payment_token_ids = fields.One2many("payment.token", "partner_id", "Payment Tokens")
    payment_token_count = fields.Integer("Count Payment Token", compute="_compute_payment_token_count")

    @api.depends("payment_token_ids")
    def _compute_payment_token_count(self):
        payment_data = self.env["payment.token"].read_group(
            [("partner_id", "in", self.ids), ("bamboraeft_tran_type", "!=", "bank")],
            ["partner_id"],
            ["partner_id"],
        )
        mapped_data = {payment["partner_id"][0]: payment["partner_id_count"] for payment in payment_data}
        for partner in self:
            partner.payment_token_count = mapped_data.get(partner.id, 0)

    payment_eft_count = fields.Integer("Count Payment EFT Token", compute="_compute_payment_eft_count")

    @api.depends("payment_token_ids")
    def _compute_payment_eft_count(self):
        payment_data = self.env["payment.token"].read_group(
            [("partner_id", "in", self.ids), ("bamboraeft_tran_type", "=", "bank")],
            ["partner_id"],
            ["partner_id"],
        )
        mapped_data = {payment["partner_id"][0]: payment["partner_id_count"] for payment in payment_data}
        for partner in self:
            partner.payment_eft_count = mapped_data.get(partner.id, 0)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade', index=True, domain=[], required=True)

    bamboraeft_account_type = fields.Selection(
        string='Bank Account Type',
        selection=BANK_ACCOUNT_TYPE,
        default='CC'
    )
    bank_transit_no = fields.Char(
        string="Bank Transit No",
    )
    bamboraeft_customer_code = fields.Char(
        string="Bambora Profile No",
    )
    bamboraeft_country_type = fields.Selection(
        string='Account Type',
        selection=BAMBORAEFT_COUNTRY_TYPE,
        default='american'
    )
    payment_token_id = fields.Many2one(
        string="Payment Token",
        comodel_name="payment.token",
        ondelete="restrict",
    )
    bamboraeft_sec_code = fields.Char('SEC Code', default="CCD")
    bamboraeft_entry_detail = fields.Char('Entry Detail Addenda Record')
    bamboraeft_status = fields.Boolean(default=False, compute="_compute_bamboraeft_status")

    @api.depends("company_id")
    def _compute_bamboraeft_status(self):
        for record in self:
            record.bamboraeft_status = False
            if record.payment_token_id:
                record.bamboraeft_status = True
            if record.company_id:
                domain = [("company_id", "in", record.company_id.ids)]
                domain += [("provider", "=", "bamboraeft")]
                acq = self.env["payment.acquirer"].sudo().search([("company_id", "in", record.company_id.ids)])
                if len(acq) > 0:
                    record.bamboraeft_status = True

    def _action_pro_profile_request(self,pro_res,rec,acq):
        if pro_res.status_code == 200:
            if pro_res.json().get("code") == 1:
                _logger.info("Bambora Profile successfully created")
                rec.bamboraeft_customer_code = pro_res.json().get("customer_code")
                try:
                    if pro_res.json().get("customer_code"):
                        pay_tkn = self.env["payment.token"].sudo()
                        token_name = rec.acc_number
                        token_name = "***" + rec.acc_number[-4:] + " (EFT)"
                        values = {
                            "bambora_token_type": "permanent",
                            "bambora_token": pro_res.json().get("customer_code"),
                            "provider": "bamboraeft",
                            "acquirer_id": acq.id,
                            "acquirer_ref": "bamboraeft",
                            "partner_id": rec.partner_id.id,
                            "name": token_name,
                        }

                        values["bamboraeft_tran_type"] = "bank"
                        _logger.info("Bambora Profile successfully created")
                        values["bambora_profile"] = pro_res.json().get("customer_code")
                        values["bambora_token_type"] = "permanent"
                        token_id = pay_tkn.create(values)
                        if token_id:
                            rec.payment_token_id = token_id.id
                    else:
                        _logger.warning("Bank Name not provided")
                except Exception as e:
                    _logger.warning("Exceptions" + str(e.args))

        else:
            _logger.warn("Customer Profile: Failure")
            message = pro_res.json().get("message")
            if pro_res.json().get("message"):
                if isinstance(pro_res.json().get("message"), list):
                    for detail in message.get("details"):
                        message += "\n" + "Field Error: %s, Message: %s" % (
                            detail.get("field"),
                            detail.get("message"),
                        )
            raise ValidationError(_(message))

    def action_create_bamboraeft_token(self):
        for rec in self:
            if (
                not rec.acc_number
                or not rec.bamboraeft_account_type
                or not rec.bamboraeft_country_type
                or not rec.bank_id
                or not rec.aba_routing
            ):
                raise ValidationError(
                    _("Please provide Account Number, Account Type, Account Code, ABA/Routing and Bank ")
                )

            domain = [("company_id", "in", rec.company_id.ids)]
            domain += [("provider", "=", "bamboraeft")]
            acq = self.env["payment.acquirer"].sudo().search(domain, limit=1)
            if acq and acq.bamboraeft_create_profile:
                comments = "Create Token for Customer-%s(%s), %s" % (rec.partner_id.name, rec.partner_id.id, "bank")
                if acq.bamboraeft_transaction_type == 'E':
                    pro_data = {
                        "language": "en",
                        "comments": comments,
                        "bank_account": {
                            "bank_account_holder": rec.acc_holder_name,
                            "account_number": rec.acc_number,
                            "bank_account_type": rec.bamboraeft_country_type,
                            "institution_number": rec.bank_id.bic,
                            "branch_number": rec.bank_transit_no,
                        },
                    }
                else:
                    pro_data = {
                            "language": "en",
                            "comments": comments,
                            "bank_account": {
                                "bank_account_holder": rec.acc_holder_name,
                                "account_number": rec.acc_number,
                                "routing_number": rec.aba_routing,
                                "bank_account_type": rec.bamboraeft_country_type,
                                "account_type": rec.bamboraeft_account_type,
                            },
                        }

                _logger.info(pprint.pformat(pro_data))
                headers = get_headers(acq.bamboraeft_merchant_id, acq.bamboraeft_profile_api)
                pro_res = requests.post(PROFILE_URL, data=json.dumps(pro_data), headers=headers)

                self._action_pro_profile_request(pro_res,rec,acq)


