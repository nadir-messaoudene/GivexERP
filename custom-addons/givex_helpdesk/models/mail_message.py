import logging
from psycopg2 import sql
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from collections import OrderedDict, defaultdict

_logger = logging.getLogger(__name__)

class Message(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, values_list):
        mails = super(Message, self).create(values_list)
        for mail in mails:
            if mail.model == 'helpdesk.ticket' and mail.message_type != 'notification':
                ticket = self.env['helpdesk.ticket'].search([('id','=',mail.res_id)])
                if ticket and ticket.stage_id.is_close and (ticket.partner_id == mail.author_id or mail.author_id.id in ticket.message_follower_ids.partner_id.ids):
                    reopen_stage = self.env['helpdesk.stage'].search([('name','=','Reopen')])
                    ticket.stage_id = reopen_stage
        return mails
