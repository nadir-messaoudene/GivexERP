# -*- encoding: utf-8 -*-
##############################################################################
#
# ingenieuxtechnologies@gmail.com
# ingenieuxtechnologies
#
##############################################################################

from odoo import api, models
from odoo.http import request
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(IrHttp, self).session_info()
        res['display_switch_company_boolean'] = self.env.user.has_group(
            'company_group_access.group_user_company_change')
        return res