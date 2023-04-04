# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import osv
from odoo.exceptions import UserError, ValidationError
try:
    from zenpy import Zenpy
    from zenpy.lib.api_objects import User, Comment, Ticket
except Exception as e:
    raise ValidationError(("Install 'zenpy' module."))
from datetime import datetime, timedelta
import os
import base64
import requests
import logging

_logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))


class HelpdeskTicketsInherit(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_id = fields.Char(string='Ticket Number')
    priority = fields.Selection(selection_add=[('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Urgent')])
    settings_account = fields.Many2one('zendesk.settings')
    is_update = fields.Boolean(string='Check update while syncing')
    is_delete = fields.Boolean(string='Check for soft delete')

    @api.model
    def create(self, values):
        res = super(HelpdeskTicketsInherit, self).create(values)
        scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler')])
        if scheduler.auto_sync_ticket:
            if 'ticket_id' in values and values['ticket_id']:
                return res
            else:
                if values['settings_account']:
                    account = self.env['zendesk.settings'].search([('id', '=', values['settings_account'])])
                    creds = {
                        'email': account.email_id,
                        'password': account.passw,
                        'subdomain': account.name
                    }

                    ticket_type = self.env['helpdesk.ticket.type'].search([('id', '=', values['ticket_type_id'])]).name

                    ''' For priority '''
                    ticket_priority_id = str(values['priority'])

                    if ticket_priority_id == '1':
                        ticket_priority = 'low'
                    elif ticket_priority_id == '2':
                        ticket_priority = 'normal'
                    elif ticket_priority_id == '3':
                        ticket_priority = 'high'
                    elif ticket_priority_id == '4':
                        ticket_priority = 'urgent'
                    else:
                        ticket_priority = ''

                    ''' For Odoo helpdesk ticket tags model '''
                    helpdesk_tag_ids = values['tag_ids'][0][2]
                    ticket_tags = []
                    for id in helpdesk_tag_ids:
                        ticket_tag = self.env['helpdesk.tag'].search([('id', '=', id)])
                        ticket_tags.append(ticket_tag.name)

                    zenpy = Zenpy(**creds)

                    if zenpy:
                        ''' For Odoo assignee field '''
                        ticket_assignee = self.env['res.users'].search([('id', '=', values['user_id'])])

                        assignee = None
                        if ticket_assignee:
                            for user in zenpy.users(role="agent"):
                                if user.name == ticket_assignee.name:
                                    assignee = user
                            if not assignee:
                                user = User(name=ticket_assignee.name, email=ticket_assignee.email, role="agent")
                                try:
                                    assignee = zenpy.users.create(user)
                                except:
                                    raise ValidationError(
                                        _("Your zendesk agent limit has been reached please increase it or change the "
                                          "assignee, which is already zendesk member"))

                        # User/Contact condition
                        if not (values['partner_name'] and values['partner_email']):
                            ticket_create = zenpy.tickets.create(
                                Ticket(
                                    subject=values['name'],
                                    description=values['description'],
                                    type=ticket_type.lower() if ticket_type else None,
                                    priority=ticket_priority,
                                    # status=ticket_status.lower(),
                                    tags=ticket_tags if ticket_tags else None,
                                    assignee=assignee,
                                )
                            )
                        else:
                            ticket_create = zenpy.tickets.create(
                                Ticket(
                                    subject=values['name'],
                                    description=values['description'],
                                    type=ticket_type.lower() if ticket_type else None,
                                    priority=ticket_priority,
                                    requester=User(name=values['partner_name'], email=values['partner_email']),
                                    tags=ticket_tags if ticket_tags else None,
                                    assignee=assignee,
                                )
                            )
                        res.ticket_id = ticket_create.ticket.id
                        ''' Stage(status) for Odoo helpdesk '''
                        if assignee:
                            ticket_stage = self.env['helpdesk.stage'].search([('name', '=', 'Open')]).id
                            res.write({
                                'stage_id': ticket_stage,
                            })
                            self.env.cr.commit()
                    else:
                        raise ValidationError(('Something went wrong please check your credentials'))
                else:
                    raise ValidationError(('Please select a company name'))

                return res
        else:
            return res

    ''' Update ticket functionality '''

    def write(self, values):

        res = super(HelpdeskTicketsInherit, self).write(values)

        if self.ticket_id and ('is_delete' in values):
            return res
        scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler')])
        if scheduler.auto_sync_ticket:
            if self.ticket_id and ('is_update' not in values or not values['is_update']):
                tags_list = []
                tags = self.tag_ids

                ''' Tags logic '''
                for tag in tags:
                    t = self.env['helpdesk.tag'].search([('id', '=', tag.id)])
                    tags_list.append(t.name)

                ''' Priority logic '''
                priority_id = self.priority

                if priority_id == '1':
                    priority = 'low'
                elif priority_id == '2':
                    priority = 'normal'
                elif priority_id == '3':
                    priority = 'high'
                elif priority_id == '4':
                    priority = 'urgent'
                else:
                    priority = None

                ''' Type and Status logic'''
                type = self.ticket_type_id.name.lower() if self.ticket_type_id.name else None
                status = self.stage_id.name.lower()

                if self.settings_account.email_id and self.settings_account.name and self.settings_account.passw:
                    auth = {
                        'email': self.settings_account.email_id,
                        'password': self.settings_account.passw,
                        'subdomain': self.settings_account.name
                    }
                    zenpy_client = Zenpy(**auth)
                    if zenpy_client:
                        assignee = None
                        if self.user_id:
                            ticket_assignee = self.env['res.users'].search([('id', '=', self.user_id.id)])

                            if ticket_assignee:
                                for user in zenpy_client.users(role="agent"):
                                    if user.name == ticket_assignee.name:
                                        assignee = user
                                if not assignee:
                                    try:
                                        user = User(name=ticket_assignee.name, email=ticket_assignee.email,
                                                    role="agent")
                                        assignee = zenpy_client.users.create(user)
                                    except:
                                        raise ValidationError(
                                            _(f"Your zendesk Agent seats has been reached and you are trying"
                                              f" to make new agent in ticket '{self.name}' please change the assignee"))

                        ticket = zenpy_client.tickets(id=int(self.ticket_id))
                        if ticket:
                            ticket.subject = values.get('name') if values.get('name') else self.name
                            ticket.name = values.get('name') if values.get('name') else self.name
                            ticket.status = status
                            ticket.type = type
                            ticket.priority = priority
                            ticket.tags.extend(tags_list)
                            ticket.assignee = assignee
                            zenpy_client.tickets.update(ticket)
                            return res
                else:
                    raise ValidationError(('Ticket not updated correctly'))
            else:
                return res
        else:
            return res

    ''' Delete ticket(s) Logic '''

    # def unlink(self):
    #     for tick in self:
    #         ticket = tick
    #         # ticket = self.env['helpdesk.ticket'].search([('ticket_id', '=', tick.ticket_id)])
    #         creds = {
    #             'email': ticket.settings_account.email_id,
    #             'password': ticket.settings_account.passw,
    #             'subdomain': ticket.settings_account.name
    #         }
    #         zenpy_client = Zenpy(**creds)
    #
    #         if zenpy_client:
    #             if ticket.settings_account.delete_zendesk:
    #                 try:
    #                     del_ticket = zenpy_client.tickets(id=int(ticket.ticket_id))
    #                     zenpy_client.tickets.delete(del_ticket)
    #                     tick.write({
    #                         'active': False,
    #                         'is_delete': True,
    #                     })
    #                     self.env.cr.commit()
    #                 except:
    #                     tick.write({
    #                         'active': False,
    #                         'is_delete': True,
    #                     })
    #                     self.env.cr.commit()
    #                     continue
    #             else:
    #                 tick.write({
    #                     'active': False,
    #                     'is_delete': True,
    #                 })
    #                 self.env.cr.commit()
    #     return self
