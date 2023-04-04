# import base64

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.osv import osv
import requests
try:
    from zenpy import Zenpy
    from zenpy.lib.api_objects import User, Comment, Ticket
except Exception as e:
    raise ValidationError(("Install 'zenpy' module."))
import os
import logging

_logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))

class TicketComments(models.Model):
    _inherit = 'mail.message'

    comment_id = fields.Char(string='Comment Id')
    created_message = fields.Boolean(string='Delete message first then create it', default=False)

    # @api.model
    # def create(self, values):
    #
    #     rec = super(TicketComments, self).create(values)
    #
    #     if 'model' in values and values['model'] == 'helpdesk.ticket':
    #         if not 'comment_id' in values and ('message_type' in values and values['message_type'] != 'notification'):
    #             complete_path = None
    #
    #             helpdesk_account_id = self.env['zendesk.sync'].search([('create_uid', '=', self.env.user.id)])
    #             ticket_id = self.env['helpdesk.ticket'].search([('id', '=', values['res_id'])]).ticket_id
    #             if helpdesk_account_id.settings_account and ticket_id:
    #                 setting = helpdesk_account_id.settings_account
    #
    #                 creds = {
    #                     'email': setting.email_id,
    #                     'password': setting.passw,
    #                     'subdomain': setting.name
    #                 }
    #
    #                 zenpy_client = Zenpy(**creds)
    #                 attachment_list = []
    #                 if zenpy_client:
    #                     attachments = self.env['ir.attachment'].search(
    #                         [('id', 'in', [i.id for i in self.attachment_ids])])
    #
    #                     for each in attachments:
    #                         attach_file_name = each.name
    #                         attach_file_data = each.sudo().read(['datas'])
    #                         directory_path = os.path.join(root_path, "files")
    #                         if not os.path.isdir(directory_path):
    #                             os.mkdir(directory_path)
    #                         file_path = os.path.join("files", attach_file_name)
    #                         complete_path = os.path.join(root_path, file_path)
    #                         with open(complete_path, "wb") as text_file:
    #                             data = "base64.decodebytes(attach_file_data[0]['datas'])"
    #                             text_file.write(data)
    #
    #                     ticket = zenpy_client.tickets(id=int(ticket_id))
    #
    #                     if ticket:
    #                         if complete_path:
    #                             upload_instance = zenpy_client.attachments.upload(complete_path)
    #                             ticket.comment = Comment(html_body=rec.body,
    #                                                      uploads=[upload_instance.token],
    #                                                      id=int(str(self.env.user.id) + str(rec.id)))
    #                         else:
    #                             ticket.comment = Comment(html_body=rec.body,
    #                                                      id=int(str(self.env.user.id) + str(rec.id)))
    #                     zenpy_client.tickets.update(ticket)
    #
    #                     rec.comment_id = int(str(self.env.user.id) + str(rec.id))
    #                     rec.sudo().write({
    #                         'created_message': True
    #                     })
    #
    #                     rec.env.cr.commit()
    #
    #                     if complete_path:
    #                         os.remove(complete_path)
    #
    #         return rec
    #     else:
    #         return rec