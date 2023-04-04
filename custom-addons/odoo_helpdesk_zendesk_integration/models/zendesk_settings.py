from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.osv import osv
import requests
import logging
import os

_logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))


class ZendeskSettings(models.Model):
    _name = 'zendesk.settings'
    _description = 'Settings'
    _rec_name = 'name'

    name = fields.Char(string='Company URL', required=True)
    email_id = fields.Char(string='Company Email', required=True)
    passw = fields.Char(string='Email Password', required=True)
    # delete_sync = fields.Boolean(string='Delete in Sync', help='Delete tickets that are deleted in Zendesk while Sync or Auto Sync in Odoo.')
    delete_zendesk = fields.Boolean(string='Delete in Zendesk', help='Delete selected tickets in Zendesk as well.')

    def test_connection(self):
        _logger.info('Test Zendesk Support Connection')
        ''' For Odoo helpdesk ticket stage model '''
        stage_list = ['New', 'Open', 'Pending', 'Solved']
        for stage in stage_list:
            ticket_stage = self.env['helpdesk.stage'].search([('name', '=', stage)])
            if not ticket_stage:
                self.env['helpdesk.stage'].create({
                    'name': stage,
                })
            self.env.cr.commit()

        ''' For Odoo helpdesk ticket type model '''
        type_remove = self.env['helpdesk.ticket.type'].search([('name', '=', 'Issue')])
        type_remove.unlink()
        type_list = ['Question', 'Incident', 'Problem', 'Task']
        for type in type_list:
            ticket_type = self.env['helpdesk.ticket.type'].search([('name', '=', type)])
            if not ticket_type:
                self.env['helpdesk.ticket.type'].create({
                    'name': type,
                })
            self.env.cr.commit()

        user = self.email_id
        pwd = self.passw
        zendesk_url = 'https://' + self.name + '.zendesk.com/api/v2/groups.json'
        try:
            response = requests.get(zendesk_url, auth=(user, pwd))
        except:
            raise ValidationError(("Authentication Credentials are not valid"))

        if response.status_code != 200:
            _logger.error('Authentication Credentials are not valid')
            raise ValidationError(('Authentication Credentials are not valid'))
        _logger.info('Successfully Connected to Zendesk')
        raise UserError(('Successfully Connected to Zendesk'))