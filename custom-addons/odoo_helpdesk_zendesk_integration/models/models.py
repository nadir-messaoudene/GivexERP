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


class InheritResUser(models.Model):
    _inherit = 'res.users'

    zendesk_id = fields.Char('Zendesk Id')

    @api.model
    def create(self, vals):
        res = super(InheritResUser, self).create(vals)
        res.partner_id.zendesk_role = 'agent'
        return res


class InheritRespartner(models.Model):
    _inherit = 'res.partner'

    zendesk_role = fields.Selection([('end-user', 'End-User'), ('agent', 'Agent')], default='end-user')
    zendesk_id = fields.Char("Zendesk ID")


class ZendeskSync(models.Model):
    _name = 'zendesk.sync'
    _description = 'Sync'
    _rec_name = 'id'

    custom_sync_active = fields.Boolean('Custom Sync Date Range')
    field_name = fields.Char('Import/Export')
    history_line = fields.One2many('sync.history', 'sync_id')
    settings_account = fields.Many2one('zendesk.settings')
    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    contact_active = fields.Boolean('Import Contacts')
    exp_contact = fields.Boolean('Export Contacts')
    ticket_active = fields.Boolean('Import Tickets')
    export_ticket = fields.Boolean('Export Tickets')
    message_active = fields.Boolean('Sync Messages')

    def unlink(self):
        raise UserError(('Deletion Not Allowed!\nJust disable the checks by editing form.'))

    def copy(self):
        raise UserError(('Duplication Not Allowed!'))


    def sync_history(self, contacts_count, no_exp_contact_counts, tickets_count, ticket_export_count, messages_count, id):
        sync_history = self.env["sync.history"]
        sync_history.create({
            "no_of_contacts": contacts_count,
            "no_exp_contacts": no_exp_contact_counts,
            "no_of_tickets": tickets_count,
            "no_exp_tickets": ticket_export_count,
            "no_of_messages": messages_count,
            "sync_id": id,
            # "document_link": path
        })
        self.env.cr.commit()

    def action_user_form_zendesk(self):
        existing_configurations = self.env['zendesk.sync'].sudo().search([])
        context = dict(self._context)
        current_logged_in_uid = self._context.get('uid')
        # existing_configurations = self.search([('for_auto_user_id', '=', current_logged_in_uid)])
        data = {
            'name': 'Import/Export',
            'res_model': 'zendesk.sync',
            'target': 'current',
            'view_mode': 'form',
            'type': 'ir.actions.act_window'
        }
        if not existing_configurations:
            return data

        data['res_id'] = existing_configurations[0].id
        return data

    @api.model
    def autosync_data(self):
        print('env user: ', self.env.user.id)
        credentials = self.env['zendesk.sync'].search([])
        print("creds: =========", credentials)
        if credentials:
            credentials[0].sync_data()

    def sync_data(self):

        contact_count = 0
        no_exp_contact_count = 0
        ticket_count = 0
        ticket_export_count = 0
        message_count = 0

        _logger.info('Start Syncing process')
        helpdesk_account_id = self.env['zendesk.settings'].search([('name', '=', self.settings_account.name)]).id

        ''' Comment due to the date feature implementation '''
        # if self.settings_account.delete_sync:
        # # get the list of zendesk ticket to be deleted
        # odoo_zd_ticket = self.env['helpdesk.ticket'].search(
        #     ['&', ('ticket_id', '!=', None), ('settings_account', '=', self.settings_account.name)])
        #
        # # get the list of zendesk ticket ids to check either zindesk ticket is deleted in zendesk or not
        # odoo_zd_tick_map = odoo_zd_ticket.mapped('ticket_id')

        creds = {
            'email': self.settings_account.email_id,
            'password': self.settings_account.passw,
            'subdomain': self.settings_account.name
        }
        print('creds: ', creds)
        try:
            zenpy_client = Zenpy(**creds)
        except Exception as e:
            raise ValidationError((str(e)))
        if zenpy_client:

            # scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler')])
            # if scheduler.active:
            #     st_date = datetime.now() - timedelta(days=1)
            #     ed_date = datetime.now()
            #     st_date_str = datetime.strftime(st_date, '%Y-%m-%d')
            #     ed_date_str = datetime.strftime(ed_date, '%Y-%m-%d')
            #     starting_date = datetime.strptime(st_date_str, '%Y-%m-%d')
            #     ending_date = datetime.strptime(ed_date_str, '%Y-%m-%d')
            # else:
            st_date = self.start_date
            ed_date = self.end_date
            # changed strptime --> strptime
            starting_date = datetime.strftime(st_date, '%Y-%m-%d %H:%M:%S')
            ending_date = datetime.strftime(ed_date, '%Y-%m-%d %H:%M:%S')
            starting_date = st_date
            ending_date = ed_date

            if self.contact_active:
                _logger.info('Start Syncing Contacts/Users')
                try:
                    users = zenpy_client.search(updated_between=[starting_date, ending_date], type='user')
                except:
                    raise ValidationError(('Date range is not Correct'))

                for user in users:
                    id = user.id
                    all_contacts_ids = self.env['res.partner'].search([('zendesk_id', '!=', False)]).mapped(
                        'zendesk_id')
                    all_users_ids = self.env['res.users'].search([('zendesk_id', '!=', False)]).mapped('zendesk_id')
                    if (str(user.id) not in all_contacts_ids) and (str(user.id) not in all_users_ids):
                        if user.role == 'agent' and not self.env['res.users'].search([('email', '=', user.email)]):
                            odoo_user = self.env['res.users'].create({
                                'name': user.name,
                                'login': user.email,
                                'email': user.email,
                                'zendesk_id': user.id,
                            })
                            self.env.cr.commit()
                            contact_count = contact_count + 1
                            _logger.info('User Created with name : ' + odoo_user.name)
                        elif user.role == 'admin' and not self.env['res.users'].search([('email', '=', user.email)]):
                            odoo_user = self.env['res.users'].create({
                                'name': user.name,
                                'login': user.email,
                                'email': user.email,
                                'zendesk_id': user.id,
                            })
                            self.env.cr.commit()
                            contact_count = contact_count + 1
                            _logger.info('User Created with name : ' + odoo_user.name)
                        elif not self.env['res.partner'].search(
                                ['&', ('email', '=', user.email), ('name', '=', user.name)]):
                            if user.role != 'admin' and user.email != 'customer@example.com':
                                odoo_contact = self.env['res.partner'].create({
                                    'name': user.name,
                                    'email': user.email,
                                    'zendesk_id': user.id,
                                    'company_type': 'company',
                                })
                                self.env.cr.commit()
                                contact_count = contact_count + 1
                                _logger.info('Contact Created with name : ' + odoo_contact.name)
                    else:
                        if user.role == 'end-user':
                            update_partner = self.env['res.partner'].search([('zendesk_id', '=', user.id)])
                            update_partner.update({
                                'name': user.name,
                                'email': user.email,
                                'zendesk_role': user.role,
                                'company_type': 'company',

                            })

                        else:
                            update_user = self.env['res.users'].search([('zendesk_id', '=', user.id)])
                            update_user.update({
                                'name': user.name,
                                'login': user.email,
                                'zendesk_id': user.id,
                            })

                    _logger.info('Contact/Users sync process done successfully')

            ''' CODE TO EXPORT CONTACTS'''
            if self.exp_contact:
                _logger.info("contacts exporting starts .....")
                contacts = self.env['res.partner'].search(
                    [('create_date', '>=', str(self.start_date)), ('zendesk_role', '=', 'end-user'),
                     ('create_date', '<=', str(self.end_date))])
                for contact in contacts:
                    _logger.info(f"Syncing contacts {contact.name}, id {contact.id}")
                    if contact.zendesk_role == 'end-user':
                        if not contact.zendesk_id:
                            try:
                                user = User(name=contact.display_name, email=contact.email,
                                            role=contact.zendesk_role)
                                created_user = zenpy_client.users.create(user)
                                contact.write({
                                    'zendesk_id': created_user.id
                                })
                                no_exp_contact_count += 1
                            except Exception as e:
                                print(e)

                        else:
                            updated_user = zenpy_client.users(id=int(contact.zendesk_id))
                            updated_user.name = contact.display_name
                            updated_user.role = contact.zendesk_role
                            updated_user = zenpy_client.users.update(updated_user)
                            contact.zendesk_id = updated_user.id

                self.env.cr.commit()

            if self.ticket_active:

                # self = self.with_context(get_sizes='tesrt')
                # print(self.env.context)
                # t = self.env.context
                # u = self.env.context.get('get_sizes', 'Test not fount')

                _logger.info('Start tickets syncing')

                try:
                    tickets = zenpy_client.search(updated_between=[starting_date, ending_date], type='ticket')
                except:
                    raise ValidationError(('Date range is not Correct'))

                for ticket in tickets:

                    # For closed ticket problem
                    if ticket.status == 'closed':
                        continue

                    ''' Comment due to the date feature implementation '''
                    # if self.settings_account.delete_sync:
                    # # done by wajahat Check the and remove the id from the list
                    # if str(ticket.id) in odoo_zd_tick_map:
                    #     odoo_zd_tick_map.remove(str(ticket.id))

                    contact_name = self.env['res.partner'].search(
                        ['&', ('name', '=', ticket.requester.name), ('email', '=', ticket.requester.email)])

                    helpdesk_ticket = self.env['helpdesk.ticket'].search(['&', ('ticket_id', '=', str(ticket.id)), (
                        'settings_account', '=', self.settings_account.name)])

                    if not helpdesk_ticket:
                        if ticket.created_at:
                            date, t, time = ticket.created_at.partition('T')
                            newtime = time.replace("Z", "")
                            requested = date + "  " + newtime
                        else:
                            requested = ''

                        ''' For Odoo helpdesk assignee functionality '''
                        if not ticket.assignee:
                            target_user = self.env['res.users'].search([('id', '=', '0')])
                        elif ticket.assignee.role == 'admin':
                            # target_user = self.env['res.users'].search([('name', '=', 'Administrator')])
                            target_user = self.env['res.users'].search([('login', '=', ticket.assignee.email)])
                            if not target_user:
                                target_user = self.env['res.users'].create({
                                    'name': ticket.assignee.name,
                                    'login': ticket.assignee.email,
                                    'email': ticket.assignee.email,
                                    'zendesk_id': ticket.assignee.id,
                                })
                            else:
                                target_user.write({
                                    'zendesk_id': ticket.assignee.id,
                                })
                        else:
                            target_user = self.env['res.users'].search([('login', '=', ticket.assignee.email)])
                            if not target_user:
                                target_user = self.env['res.users'].create({
                                    'name': ticket.assignee.name,
                                    'login': ticket.assignee.email,
                                    'email': ticket.assignee.email,
                                    'zendesk_id': ticket.assignee.id,
                                })
                            else:
                                target_user.write({
                                    'zendesk_id': ticket.assignee.id,
                                })
                        ''' For Odoo helpdesk ticket contact/customer field '''
                        contact_id = self.env['res.partner'].search(
                            ['&', ('name', '=', ticket.requester.name), ('email', '=', ticket.requester.email)]).id

                        ''' In case of contact not created before '''
                        if not contact_id:
                            odoo_contact = self.env['res.partner'].create({
                                'name': ticket.requester.name,
                                'email': ticket.requester.email,
                                'zendesk_id': ticket.requester.id,
                                'company_type': 'company',
                            })
                            self.env.cr.commit()
                            _logger.info('Contact Created with name : ' + odoo_contact.name)
                            contact_id = self.env['res.partner'].search(
                                ['&', ('name', '=', ticket.requester.name), ('email', '=', ticket.requester.email)]).id

                        ''' For Odoo helpdesk ticket priority field '''
                        if ticket.priority == 'low':
                            priority_id = '1'
                        elif ticket.priority == 'normal':
                            priority_id = '2'
                        elif ticket.priority == 'high':
                            priority_id = '3'
                        elif ticket.priority == 'urgent':
                            priority_id = '4'
                        else:
                            priority_id = '0'

                        ''' For Odoo helpdesk ticket stage model '''
                        ticket_stage = self.env['helpdesk.stage'].search([('name', '=', ticket.status.capitalize())])

                        if not ticket_stage:
                            ticket_stage = self.env['helpdesk.stage'].create({
                                'name': ticket.status.capitalize(),
                            })

                        ''' For Odoo helpdesk ticket tags model '''
                        helpdesk_tags = ticket.tags
                        tag_ids = []
                        for tag in helpdesk_tags:
                            ticket_tag = self.env['helpdesk.tag'].search([('name', '=', tag)])
                            if ticket_tag:
                                tag_ids.append(ticket_tag.id)
                            else:
                                ticket_tag = self.env['helpdesk.tag'].create({
                                    'name': tag,
                                })
                                tag_ids.append(ticket_tag.id)

                        ''' For Odoo helpdesk ticket type model '''
                        if ticket.type is None:
                            helpdesk_ticket = self.env['helpdesk.ticket'].create({
                                'ticket_id': str(ticket.id),
                                'description': ticket.description if ticket.description else None,
                                'name': ticket.subject if ticket.subject else None,
                                'stage_id': ticket_stage.id if ticket_stage.id else None,
                                'priority': priority_id,
                                'user_id': target_user.id if target_user.id else None,
                                'partner_id': contact_id,
                                'settings_account': helpdesk_account_id,
                                'tag_ids': [[6, False, tag_ids]] if tag_ids else None,
                            })
                            self.env.cr.commit()
                            ticket_count = ticket_count + 1
                            _logger.info('Ticket Created with id : ' + str(helpdesk_ticket.id))
                        else:
                            ticket_type = self.env['helpdesk.ticket.type'].search(
                                [('name', '=', ticket.type.capitalize())])

                            if not ticket_type:
                                ticket_type = self.env['helpdesk.ticket.type'].create({
                                    'name': ticket.type.capitalize(),
                                })

                            helpdesk_ticket = self.env['helpdesk.ticket'].create({
                                'ticket_id': str(ticket.id),
                                'description': ticket.description if ticket.description else None,
                                'name': ticket.subject if ticket.subject else None,
                                'stage_id': ticket_stage.id if ticket_stage.id else None,
                                'priority': priority_id,
                                'ticket_type_id': ticket_type.id,
                                'user_id': target_user.id if target_user.id else None,
                                'partner_id': contact_id,
                                'settings_account': helpdesk_account_id,
                                'tag_ids': [[6, False, tag_ids]] if tag_ids else None,
                            })
                            self.env.cr.commit()
                            ticket_count = ticket_count + 1
                            _logger.info('Ticket Created with id : ' + str(helpdesk_ticket.id))
                    else:
                        if ticket.created_at:
                            date, t, time = ticket.created_at.partition('T')
                            newtime = time.replace("Z", "")
                            requested = date + "  " + newtime
                        else:
                            requested = ''

                        ''' Update logic for Odoo Helpdesk here '''

                        ''' For Odoo helpdesk assignee functionality '''
                        user_obj = self.env['res.users']
                        if not ticket.assignee:
                            target_user = self.env['res.users'].search([('id', '=', '0')])
                        elif ticket.assignee.role == 'admin':
                            # target_user = self.env['res.users'].search([('name', '=', 'Administrator')])
                            target_user = self.env['res.users'].search([('login', '=', ticket.assignee.email)])
                        else:
                            target_user = self.env['res.users'].search([('login', '=', ticket.assignee.email)])

                        ''' For Odoo helpdesk ticket priority field '''
                        if ticket.priority == 'low':
                            priority_id = '1'
                        elif ticket.priority == 'normal':
                            priority_id = '2'
                        elif ticket.priority == 'high':
                            priority_id = '3'
                        elif ticket.priority == 'urgent':
                            priority_id = '4'
                        else:
                            priority_id = '0'

                        ''' For Odoo helpdesk ticket stage model '''
                        ticket_stage = self.env['helpdesk.stage'].search([('name', '=', ticket.status.capitalize())])

                        if not ticket_stage:
                            ticket_stage = self.env['helpdesk.stage'].create({
                                'name': ticket.status.capitalize(),
                            })

                        ''' For Odoo helpdesk ticket tags model '''
                        helpdesk_tags = ticket.tags
                        tag_ids = []
                        for tag in helpdesk_tags:
                            ticket_tag = self.env['helpdesk.tag'].search([('name', '=', tag)])
                            if ticket_tag:
                                tag_ids.append(ticket_tag.id)
                            else:
                                ticket_tag = self.env['helpdesk.tag'].create({
                                    'name': tag,
                                })
                                tag_ids.append(ticket_tag.id)

                        ''' Update logic for Odoo helpdesk tickets '''
                        if ticket.type is None:
                            helpdesk_ticket.write({
                                'name': ticket.subject if ticket.subject else None,
                                'stage_id': ticket_stage.id if ticket_stage.id else None,
                                'priority': priority_id,
                                'is_update': True,
                                'user_id': target_user.id if target_user.id else None,
                                'tag_ids': [[6, False, tag_ids]] if tag_ids else None,
                            })
                            self.env.cr.commit()
                            # ticket_count = ticket_count + 1
                            _logger.info('Ticket Updated with id : ' + str(helpdesk_ticket.id))
                        else:
                            ticket_type = self.env['helpdesk.ticket.type'].search(
                                [('name', '=', ticket.type.capitalize())])

                            if not ticket_type:
                                ticket_type = self.env['helpdesk.ticket.type'].create({
                                    'name': ticket.type.capitalize(),
                                })
                            helpdesk_ticket.write({
                                'name': ticket.subject if ticket.subject else None,
                                'stage_id': ticket_stage.id if ticket_stage.id else None,
                                'priority': priority_id,
                                'is_update': True,
                                'ticket_type_id': ticket_type.id,
                                'user_id': target_user.id if target_user.id else None,
                                'tag_ids': [[6, False, tag_ids]] if tag_ids else None,
                            })
                            self.env.cr.commit()
                            # ticket_count = ticket_count + 1
                            _logger.info('Ticket Updated with id : ' + str(helpdesk_ticket.id))

                _logger.info('All Tickets Created/Updated')

            "=================> Code for ticket export start here <============================"

            if self.export_ticket:
                _logger.info('Start ticket export syncing')
                not_added_tickets = self.env['helpdesk.ticket'].search(
                    [('ticket_id', '=', False), ('create_date', '>=', self.start_date),
                     ('create_date', '<=', self.end_date)])
                not_updated_tickets = self.env['helpdesk.ticket'].search([('create_date', '>=', self.start_date),
                                                                          ('create_date', '<=', self.end_date),
                                                                          ('ticket_id', '!=', False)])

                zen_all_agents = zenpy_client.search(role='agent')
                zen_all_admins = zenpy_client.search(role='admin')
                all_agents = [user for user in zen_all_agents]
                all_admin = [user for user in zen_all_admins]
                all_admin_agents_recs = all_agents + all_admin
                for rec in not_updated_tickets:
                    _logger.info(f"Syncing of ticket {rec.name} which id is {rec.id}")
                    ''' For priority '''
                    ticket_priority_id = str(rec.priority) if rec.priority else ''

                    if ticket_priority_id == '1':
                        ticket_priority = 'low'
                    elif ticket_priority_id == '2':
                        ticket_priority = 'normal'
                    elif ticket_priority_id == '3':
                        ticket_priority = 'high'
                    # elif ticket_priority_id == '4':
                    #     ticket_priority = 'urgent'
                    else:
                        ticket_priority = 'urgent'

                    zenpy_e = Zenpy(**creds)
                    type = rec.ticket_type_id.name.lower() if rec.ticket_type_id.name else None
                    status = rec.stage_id.name.lower()
                    tags_list = []
                    tags = rec.tag_ids
                    ''' Tags logic '''
                    for tag in tags:
                        t = rec.env['helpdesk.tag'].search([('id', '=', tag.id)])
                        tags_list.append(t.name)

                    ticket_assignee = self.env['res.users'].search([('id', '=', rec.user_id.id)])
                    assignee = None
                    if ticket_assignee:
                        if ticket_assignee.zendesk_id:
                            for user in all_admin_agents_recs:
                                t = user.id
                                p = ticket_assignee.zendesk_id
                                if str(user.id) == ticket_assignee.zendesk_id:
                                    assignee = user
                        else:
                            # if not assignee:
                            user = User(name=ticket_assignee.name, email=ticket_assignee.email, role="agent")
                            try:
                                assignee = zenpy_e.users.create(user)
                            except Exception as e:
                                print(e)
                                continue
                                # raise ValidationError(_(f"Your zendesk agent limit has been completed please "
                                #                         f"increase it or change the "
                                #                         f"assignee '{rec.user_id.name}' in ticket '{rec.name}',"
                                #                         ))
                    if rec.ticket_id:
                        ticket = zenpy_e.tickets(id=int(rec.ticket_id))
                        if ticket:
                            ticket.subject = rec.name
                            ticket.name = rec.name
                            ticket.status = status
                            ticket.type = type
                            ticket.priority = ticket_priority
                            ticket.tags.extend(tags_list)
                            ticket.assignee = assignee
                            zenpy_e.tickets.update(ticket)
                            # return rec
                    else:
                        continue

                if not_added_tickets:
                    zenpy_e = Zenpy(**creds)
                    for rec in not_added_tickets:
                        _logger.info(f"Adding Ticket Name: {rec.name} which id: {rec.id}")
                        ticket_tags = []
                        for id in rec.tag_ids:
                            ticket_tag = self.env['helpdesk.tag'].search([('id', '=', id.id)])
                            ticket_tags.append(ticket_tag.name)

                        ticket_assignee = self.env['res.users'].search([('id', '=', rec.user_id.id)])
                        assignee = None
                        if ticket_assignee:
                            if ticket_assignee.zendesk_id:
                                for user in all_admin_agents_recs:
                                    if str(user.id) == ticket_assignee.zendesk_id:
                                        assignee = user
                            else:
                                # if not assignee:
                                user = User(name=ticket_assignee.name, email=ticket_assignee.email, role="agent")
                                try:
                                    assignee = zenpy_e.users.create(user)
                                except Exception as e:
                                    print(e)
                                    continue
                                    # raise ValidationError(_(f"Your zendesk agent limit has been completed please "
                                    #                         f"increase it or change the "
                                    #                         f"assignee '{rec.user_id.name}' in ticket '{rec.name}',"
                                    #                         ))
                        ''' For priority '''
                        ticket_priority_id = str(rec.priority) if rec.priority else ''

                        if ticket_priority_id == '1':
                            ticket_priority = 'low'
                        elif ticket_priority_id == '2':
                            ticket_priority = 'normal'
                        elif ticket_priority_id == '3':
                            ticket_priority = 'high'
                        else:
                            ticket_priority = 'urgent'

                        ticket_create = zenpy_e.tickets.create(
                            Ticket(
                                subject=rec.name,
                                description=rec.description,
                                type=rec.ticket_type_id.name.lower() if rec.ticket_type_id else None,
                                priority=ticket_priority,
                                # status=status,
                                tags=ticket_tags if ticket_tags else None,
                                assignee=assignee,
                            )
                        )
                        rec.write({
                            'ticket_id': ticket_create.ticket.id
                        })
                        ticket_export_count += 1
                        self.env.cr.commit()
                        # rec.ticket_id = ticket_create.ticket.id

            if self.message_active:
                try:
                    tickets = zenpy_client.search(updated_between=[starting_date, ending_date], type='ticket')
                except:
                    raise ValidationError(('Date range is incorrect!'))

                ticket_ids = [ticket.id for ticket in tickets]
                # get the messages from helpdesk
                _logger.info('Messages Syncing')
                for id in ticket_ids:
                    helpdesk_ticket = self.env['helpdesk.ticket'].search([('ticket_id', '=', str(id))])
                    if helpdesk_ticket:
                        comment_ids = []
                        # messages = self.env['mail.message'].search(
                        #     ['&', ('res_id', '=', str(helpdesk_ticket.id)), ('created_message', '=', True)])
                        # if messages:
                        #     _logger.info('Delete messages')
                        #     for msg in messages:
                        #         msg.sudo().unlink()
                        comments = zenpy_client.tickets.comments(id)
                        for comment in comments:
                            comment_id = self.env['mail.message'].search(
                                ['&', ('comment_id', '=', comment.id), ('res_id', '=', str(helpdesk_ticket.id))])
                            if comment_id or comment.body == 'Ticket created':
                                continue
                            else:
                                author_id = self.env['res.partner'].search(
                                    ['&', ('email', '=', comment.author.email), ('name', '=', comment.author.name)]).id
                                helpdesk_comment = self.env['mail.message'].create({
                                    'comment_id': str(comment.id),
                                    'message_type': 'comment',
                                    'body': comment.body,
                                    'create_date': comment.created_at,
                                    'display_name': comment.author.name if comment.author.name else None,
                                    'email_from': comment.author.email if comment.author.email else None,
                                    'author_id': author_id,
                                    'model': 'helpdesk.ticket',
                                    'res_id': helpdesk_ticket.id
                                })
                                # comment_ids.append(helpdesk_comment.id)
                                helpdesk_ticket.env.cr.commit()
                                message_count = message_count + 1
                                _logger.info('Message Created with id : ' + str(helpdesk_comment.id))
                _logger.info('Ticket messages process complete')
            # if any([contact_count,no_exp_contact_count,ticket_count,ticket_export_count,message_count]):
            print('id',self.id)
            self.sync_history(contact_count, no_exp_contact_count, ticket_count, ticket_export_count, message_count, self.id)
        else:
            raise ValidationError(('Credentials are not valid'))

        ''' Comment due to the date feature implementation '''
        # Delete tickets if they are not found in zendesk
        # if self.settings_account.delete_sync:
        #     _logger.info('Delete Ticket')
        #     if odoo_zd_tick_map:
        #         odoo_tickets = odoo_zd_ticket.search([('ticket_id', 'in', odoo_zd_tick_map)])
        #         if odoo_tickets:
        #             odoo_tickets.sudo().unlink()


class TicketRestore(models.Model):
    _name = 'ticket.restore'
    _description = 'Restore'
    _rec_name = 'id'

    restore_tickets = fields.Boolean('Restore Tickets')
    field_name = fields.Char('Tickets Restore')

    def restore(self):
        if self.restore_tickets:
            try:
                tickets = self.env['helpdesk.ticket'].search([('active', '=', False)])

                for ticket in tickets:
                    ticket.write({
                        'active': True,
                        'is_delete': False,
                    })
                self.env.cr.commit()
            except Exception as e:
                raise Warning((str(e)))

    def unlink(self):
        # raise UserError(('Not allowed to delete, Just diable the scheduler by editing form.'))
        raise UserError(('Deletion Not Allowed!\nJust disable the check by editing form.'))

class SyncHistory(models.Model):
    _name = 'sync.history'
    _description = 'History'
    _rec_name = 'id'
    _order = 'sync_date desc'
    sync_id = fields.Many2one('zendesk.sync', string='Partner Reference', required=True, ondelete='cascade', index=True,
                              copy=False)
    # sync_id = fields.Many2one('zendesk.sync', string='Partner Reference', ondelete='cascade', index=True, copy=False)
    sync_date = fields.Datetime(string='Date', readonly=True, required=True, default=fields.Datetime.now)
    no_of_contacts = fields.Integer(string='Import Contacts', readonly=True)
    no_exp_contacts = fields.Integer(string='Export Contacts', readonly=True)
    no_of_tickets = fields.Integer(string='Import Tickets', readonly=True)
    no_exp_tickets = fields.Integer(string='Export Tickets', readonly=True)
    no_of_messages = fields.Integer(string='Messages', readonly=True)
    document_link = fields.Char(string='Document Link', readonly=True)

    def sync_data(self):
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "log_file",
            'target': 'new',
            'url': self.document_link
        }
        return client_action
