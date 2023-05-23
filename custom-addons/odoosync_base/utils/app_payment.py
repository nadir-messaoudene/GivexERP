# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from os import access

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

STATECODE_REQUIRED_COUNTRIES = ["US", "CA", "PR ", "IN"]


class AppPayment:
    def __init__(self, service_name, service_type, service_key):
        self.service_name = service_name
        self.service_type = service_type
        self.service_key = service_key
        self.data = {}

    def payment_process(self,**kwargs):
        """[summary]"""

        formatted_response = {"url": []}

        url = "/api/v1/services/payment_gateway/"
        request_type = "POST"
        headers = {
            "Content-Type": "application/json",
            "X-Service-Key": self.service_key,
        }
        data = self.__dict__

        try:
            formatted_response = request.env["omnisync.connector"].omnisync_api_call(
                headers=headers,
                url=url,
                request_type=request_type,
                data=data,
                company_id=kwargs['company_id']
                # debug_logging=debug_logging,
                # access_token=access_token
            )

            _logger.info("formatted_response ====>>>>", formatted_response)
            formatted_response['error'] = formatted_response.get("errors") if formatted_response.get("errors") else None

            return formatted_response

        except Exception as e:
            formatted_response['errors_message'] = e.args[0]
        return formatted_response
