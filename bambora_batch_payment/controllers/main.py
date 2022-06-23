###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import logging
import random
import string

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request
from werkzeug import urls, utils

_logger = logging.getLogger(__name__)


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


class BamboraEftController(http.Controller):
    _notify_url = "/payment/bamboraeft/ipn/"
    _return_url = "/payment/bamboraeft/return/"
    _cancel_url = "/payment/bamboraeft/cancel/"

    @http.route(
        [
            "/payment/bamboraeft/return/",
            "/payment/bamboraeft/cancel/",
        ],
        type="http",
        auth="public",
        csrf=False,
    )
    def bamboraeft_form_feedback(self, **post):
        if post:
            request.env["payment.transaction"].sudo().form_feedback(post, "bambora")
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return request.render(
            "bambora_batch_payment.payment_bamboraeft_redirect",
            {"return_url": urls.url_join(base_url, "/payment/process")},
        )

    # --------------------------------------------------
    # SERVER2SERVER RELATED CONTROLLERS
    # --------------------------------------------------

    @http.route(
        ["/payment/bamboraeft/s2s/create_json_3ds"],
        type="json",
        auth="public",
        csrf=False,
    )
    def bamboraeft_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        _logger.info("bambora_s2s_create_json_3ds")
        _logger.info(request.httprequest.url)
        token = False
        acquirer = request.env["payment.acquirer"].browse(int(kwargs.get("acquirer_id")))
        try:
            if not kwargs.get("partner_id"):
                kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
            token = acquirer.s2s_process(kwargs)
        except ValidationError as e:
            message = e.args[0]
            if isinstance(message, dict) and "missing_fields" in message:
                if request.env.user._is_public():
                    message = _("Please sign in to complete the payment.")
                    if (
                        request.env["ir.config_parameter"]
                        .sudo()
                        .get_param("auth_signup.allow_uninvited", "False")
                        .lower()
                        == "false"
                    ):
                        message += _(
                            " If you don't have any account, ask your salesperson to grant you a portal access. "
                        )
                else:
                    msg = _(
                        "The transaction cannot be processed because some contact details are missing or invalid: "
                    )
                    message = msg + ", ".join(message["missing_fields"]) + ". "
                    message += _("Please complete your profile. ")

            return {"error": message}

        if not token:
            res = {
                "result": False,
            }
            return res

        res = {
            "result": True,
            "id": token.id,
            "short_name": token.short_name,
            "3d_secure": False,
            "verified": True,
        }
        _logger.info(res)
        return res

    @http.route(["/payment/bamboraeft/s2s/create"], type="http", auth="public")
    def bamboraeft_s2s_create(self, **post):
        acquirer_id = int(post.get("acquirer_id"))
        acquirer = request.env["payment.acquirer"].browse(acquirer_id)
        acquirer.s2s_process(post)
        return utils.redirect("/payment/process")

    @staticmethod
    def get_payment_transaction_ids():
        # return the ids and not the recordset, since we might need to
        # sudo the browse to access all the record
        # I prefer to let the controller chose when to access to payment.transaction using sudo
        return request.session.get("__payment_tx_ids__", [])

    @http.route(["/payment/process"], type="http", auth="public", website=True, sitemap=False)
    def payment_status_page(self, **kwargs):
        # When the customer is redirect to this website page,
        # we retrieve the payment transaction list from his session
        tx_ids_list = self.get_payment_transaction_ids()
        payment_transaction_ids = request.env["payment.transaction"].sudo().browse(tx_ids_list).exists()
        payment_tx_ids = payment_transaction_ids.ids
        if len(payment_tx_ids) > 0:
            payment_tx_ids = sorted(payment_tx_ids, reverse=True)

        render_ctx = {
            "payment_tx_ids": payment_tx_ids,
        }
        acquirer_ids = []
        for tx_id in payment_transaction_ids:
            if tx_id.acquirer_id.provider == "bamboraeft":
                acquirer_ids += tx_id.acquirer_id.ids if tx_id.acquirer_id.id not in acquirer_ids else []
        if len(acquirer_ids) == 1:
            return request.render("bambora_batch_payment.bamboraeft_payment_process_page", render_ctx)
        # _logger.info("tx_ids_list ===>>>" + str(tx_ids_list))
        # _logger.info("payment_transaction_ids ===>>>" + str(payment_transaction_ids))
        # _logger.info("render_ctx ===>>>" + str(render_ctx))
        return request.render("payment.payment_process_page", render_ctx)
