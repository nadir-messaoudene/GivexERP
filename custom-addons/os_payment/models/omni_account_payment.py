# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo.addons.odoosync_base.utils.helper import image_processing
from odoo import api, fields, models

import requests
import logging
_logger = logging.getLogger(__name__)


class OmniAccountPayment(models.Model):
    _inherit = "omni.account"

    acquirer_ids = fields.One2many(
        string="Payment Acquirers",
        comodel_name="payment.acquirer",
        inverse_name="account_id",
    )
    journal_ids = fields.One2many(
        string="Account Journals",
        comodel_name="account.journal",
        inverse_name="account_id"
    )

    def process_subscriptions(self, res_json):
        kwargs = super(OmniAccountPayment, self).process_subscriptions(res_json)
        for subscription in kwargs["all_subscriptions"].get("payment"):
            if not subscription.get("service_name").endswith("cloud"):
                kwargs = self.process_payment_subscriptions(kwargs, subscription)
            else:
                kwargs = self.process_pos_payment_subscriptions(kwargs,subscription)
        return kwargs

    def process_payment_subscriptions(self, kwargs, subscription):
        """[summary]

        Args:
            kwargs ([type]): [description]
            subscription ([type]): [description]
        """

        payment_acquirer = self.env["payment.acquirer"].sudo()
        domain = [("token", "=", subscription.get("service_key"))]
        existing_service = payment_acquirer.search(domain, limit=1)
        if not existing_service:
            kwargs["messages"] += "\n" + subscription.get("service_name").upper()

            created_val = {
                "name": subscription.get("service_name").upper(),
                "provider": subscription.get("service_name"),
                "company_id": self.company_id.id,
                "omnisync_active": True,
                "account_id": self.id,
                "token": subscription.get("service_key"),
                "module_id": self.env['ir.module.module'].sudo().search([("name", "=", 'os_payment')], limit=1).id
            }
            if subscription.get("service_name") == 'moneris':
                created_val.update({
                    "provider": "monerischeckout",
                    "name": "Moneris Checkout",
                    "display_as": "Moneris Checkout",
                    "inline_form_view_id": self.env.ref("os_payment.moneris_inline_form").id,
                    "image_128": image_processing(image_path="os_payment/static/src/img/moneris_checkout"
                                                             "/moneris_checkout.png")
                })
            elif subscription.get("service_name") == 'bambora_checkout':
                created_val.update({
                    "provider": "bamborachk",
                    "name": "Bambora Checkout",
                    "display_as": "Bambora Checkout",
                    "inline_form_view_id": self.env.ref(
                        "os_payment.bamborachk_inline_form"
                    ).id,
                    # "payment_flow":"s2s"
                    "image_128": image_processing(image_path="os_payment/static/src/img/bambora_checkout/icon.png")

                })

            try:
                created_payment = payment_acquirer.create(created_val)
                created_payment._cr.commit()
                _logger.info("Payment Method Creation Complete: ===>>>{}".format(created_payment))
            except Exception as e:
                _logger.info("Payment Method Creation Failed")
                kwargs["error_messages"] += (
                        subscription.get("service_name").upper() + f": Payment Method Creation Failed\nReason: {e}"
                )
        else:
            kwargs["error_messages"] += (
                subscription.get("service_name").upper() + " already exists!"
            )

        # if subscription.get("service_name").endswith("cloud"):
        #     kwargs = self.process_pos_payment_subscriptions(kwargs, subscription)

        return kwargs


    def process_pos_payment_subscriptions(self, kwargs, subscription):
        journal = self.env['account.journal']
        domain = [("token", "=", subscription.get("service_key"))]
        existing_service = journal.search(domain, limit=1)

        if not existing_service:
            journal = self.env['account.journal'].search([("type","=","bank"),('company_id','=',self.company_id.id)],limit=1)
            kwargs["messages"] += "\n" + subscription.get("service_name").upper()
            if subscription.get("service_name") == 'clover_cloud':
                server_url = self.server_url + subscription.get('detail')
                headers = {"Authorization": "Token %s" % (self.token)}
                response = requests.request("GET", server_url, headers=headers)
                if response.status_code == 200:
                    res_json = response.json()
                    new_clover_journal = journal.copy()
                    new_clover_journal.write({
                        "name": subscription.get("service_name").upper(),
                        "omnisync_active": True,
                        "account_id": self.id,
                        "token": subscription.get("service_key"),
                        "use_clover_terminal": True,
                        'clover_server_url': res_json.get('clover_server_url'),
                        'clover_config_id': res_json.get('clover_config_id'),
                        'clover_jwt_token': res_json.get('clover_token'),
                        'clover_merchant_id': res_json.get('clover_merchant_id')

                    })
            if subscription.get("service_name") == 'moneris_cloud':
                existing_moneris= journal.search([("use_cloud_terminal","=",True)])
                server_url = self.server_url + subscription.get('detail')
                headers = {"Authorization": "Token %s" % (self.token)}
                response = requests.request("GET", server_url, headers=headers)
                if response.status_code == 200:
                    res_json = response.json()
                    new_moneris_journal = journal.copy()
                    new_moneris_journal.write({
                        "name": subscription.get("service_name").upper()+"-"+str(len(existing_moneris)+1),
                        "use_cloud_terminal": True,
                        "omnisync_active": True,
                        "account_id": self.id,

                        "token": subscription.get("service_key"),
                        'cloud_store_id': res_json.get('store_id'),
                        'cloud_api_token': res_json.get('api_token'),
                        'cloud_terminal_id': res_json.get('terminal_id'),
                        'cloud_pairing_token': "77777"

                    })
        else:
            kwargs["error_messages"] += (
                    subscription.get("service_name").upper() + " already exists!"
            )
        return kwargs
