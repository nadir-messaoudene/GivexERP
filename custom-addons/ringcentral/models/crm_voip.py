# See LICENSE file for full copyright and licensing details.

import time
import base64
import tempfile
import re
import requests
from datetime import datetime
from datetime import timedelta
from odoo import models, fields, api, tools, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, \
    DEFAULT_SERVER_DATETIME_FORMAT


class CrmPhonecallAbout(models.Model):
    _name = "crm.phonecall.about"

    name = fields.Char('Reason of the call', required=True)


class CrmPhonecall(models.Model):

    _name = "crm.phonecall"
    _order = "id DESC"

    name = fields.Char('Call Summary', required=True)

    type = fields.Selection(
        [('in_bound', 'In Bound'), ('out_bound', 'Out Bound'),
         ('message', 'Message'),
         ('receive', 'Receive'),
         ('sent', 'Sent')], string='Type')
    ringcentral_message_id = fields.Char('Ringcentral Message Id')
    ringcentral_call_url = fields.Char('Ringcentral Call Recording URL')
    ringcentral_call_id = fields.Char('Ringcentral Call Record  Id')
    tag_ids = fields.Many2many('in.out.tagged.documented',
                               'rel_tagged_documented', 'tagged_documented_id',
                               'phoncall_id', 'Tag')
    date = fields.Datetime('Date')
    crm_phonecall_about_id = fields.Many2one('crm.phonecall.about',
                                             'Phonecall about?')
    user_id = fields.Many2one('res.users', 'Responsible')
    partner_id = fields.Many2one('res.partner', 'Contact')
    company_id = fields.Many2one('res.company', 'Company')
    description = fields.Text('Description')
    duration = fields.Float('Duration',
                            help="Duration in minutes and seconds.")
    partner_phone = fields.Char('Phone')
    partner_mobile = fields.Char('Mobile')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], string='priority')
    team_id = fields.Many2one('crm.team', 'Sales Team', index=True,
                              help="Sales team to which Case belongs to.")
    categ_id = fields.Many2one('crm.phonecall.category', 'Category')
    in_queue = fields.Boolean('In Call Queue', default=True)
    sequence = fields.Integer(
        'Sequence',
        index=True,
        help="Gives the sequence order when displaying a list of Phonecalls.")
    start_time = fields.Integer("Start time")
    state = fields.Selection([
        ('pending', 'Not Held'),
        ('cancel', 'Cancelled'),
        ('open', 'To Do'),
        ('done', 'Held'),
    ], string='Status', readonly=True, track_visibility='onchange',
        help='The status is set to To Do, when a case is created.\n'
             'When the call is over, the status is set to Held.\n'
             'If the call is not applicable anymore,'
             'the status can be set to Cancelled.')
    opportunity_id = fields.Many2one('crm.lead', 'Lead/Opportunity',
                                     ondelete='cascade',
                                     track_visibility='onchange')
    check_notification = fields.Boolean('Check notification')
    crm_call_activity_ids = fields.One2many('crm.call.activity',
                                            'crm_phonecall_id',
                                            'Crm Call Activity')
    is_recording = fields.Boolean(string='IS Recording')
    attachment_ids = fields.Many2many('ir.attachment',
                                      'phonecall_attachment_rel',
                                      'phonecall_id', 'attachment_id',
                                      string="SMS attachment")
    _defaults = {
        'date': fields.Datetime.now(),
        'priority': '1',
        'state': 'open',
        'user_id': lambda self: self and self.env.user.id,
        'team_id': lambda self: self and self.env[
            'crm.team']._get_default_team_id(),
        'active': 1
    }

    @api.model
    def synch_data(self, rec_li):
        for rec in rec_li:

            if rec.get('id'):
                data = self.search(
                    [('ringcentral_call_id', '=', rec.get('id'))])
                if not data:
                    if rec.get('recording'):
                        user_id = self.env.user
                        if user_id.company_id and \
                                user_id.company_id.ringcentral_service_uri:
                            url = user_id.company_id.ringcentral_service_uri
                            url = url.split('/login/')[0]
                        else:
                            url = ''
                        if rec.get('recording').get('type') == 'Automatic':
                            rec_type = 'Auto'
                        else:
                            rec_type = rec.get('recording').get('type')
                        str_url = url + '''/mobile/media?cmd=downloadMessage&msgid=''' + \
                            rec.get('recording').get('id') + \
                            '''&useName=true&time=''' + '1554700788480' + \
                            '&msgExt=&msgNum=' + rec.get('from').get(
                                'phoneNumber') + '&msgDir=' + rec.get('direction') + \
                            '&msgRecType=' + rec_type + '&msgRecId=' + rec.get(
                                'recording').get('id') + '''&type=1&download=1&saveMsg=&file=.mp3'''
                    vals = {
                        'name': rec.get('to').get('phoneNumber'),
                        'partner_phone': rec.get('from').get('phoneNumber'),
                        'date': datetime.today(),
                        'description': rec.get('reasonDescription'),
                        'duration': rec.get('duration'),
                        'ringcentral_call_id': rec.get('id'),
                    }
                    leg_li = []
                    for leg in rec.get('legs'):
                        # crm_call_activity_ids
                        val = {
                            'name': leg.get('action'),
                            'call_type': leg.get('direction'),
                            'leg_type': leg.get('legType'),
                            'from_number': leg.get('from').get('phoneNumber'),
                            'to_number': leg.get('to').get('phoneNumber')
                        }
                        leg_li.append((0, 0, val))
                    if rec.get('direction'):
                        if rec.get('direction') == 'Inbound':
                            vals['type'] = 'in_bound'
                        elif rec.get('direction') == 'Outbound':
                            vals['type'] = 'out_bound'
                    if rec.get('recording'):
                        vals.update({
                            'ringcentral_call_url': str_url,
                            'is_recording': True
                        })
                    vals.update({
                        'crm_call_activity_ids': leg_li
                    })
                    self.create(vals)

    @api.model
    def get_service_uri(self):
        return self.env.user.company_id.ringcentral_service_uri

    @api.model
    def ac_search_read(self):
        rec_message = self.search([])
        rec_message_id = rec_message.mapped('ringcentral_message_id')
        return rec_message_id

    @api.model
    def create_message(self, list_type):
        user_id = self.env.user
        for rec_vals in list_type:
            rec_data = self.search(
                [('ringcentral_message_id', '=', rec_vals.get('id'))])
            if not rec_data:
                vals = {
                    'name': rec_vals.get('from').get('phoneNumber'),
                    'partner_phone': rec_vals.get('to')[0].get('phoneNumber'),
                    'description': rec_vals.get('subject'),
                    'ringcentral_message_id': rec_vals.get('id')
                }
                if rec_vals.get('direction') == 'Outbound':
                    vals.update({'type': 'sent'})
                else:
                    vals.update({'type': 'receive'})
                attachment_list = []
                for attachment in rec_vals.get('attachments'):
                    if attachment.get('type') == 'MmsAttachment':
                        auth_str = "Bearer  " + user_id.ringcentral_access_token
                        headers = {
                            'accept': 'application/json',
                            'authorization': auth_str,
                        }
                        response = requests.get(
                            attachment.get('uri'), headers=headers)
                        path = tempfile.mktemp('.' + 'image.png')
                        file_path = open(path, "wb")
                        file_path.write(response.content)
                        file_path.close()
                        buf = base64.encodestring(open(path, 'rb').read())
                        attachment_list.append((0, 0, {
                            'name': attachment.get('fileName') or 'image.png',
                            'type': 'binary',
                            'datas': buf,
                        }))
                if attachment_list:
                    vals.update({'attachment_ids': attachment_list})
                self.create(vals)

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        self.ensure_one()
        if self.partner_id:
            self.partner_phone = self.partner_id.phone
            self.partner_mobile = self.partner_id.mobile

    @api.model
    def create(self, values):
        if values.get('date') and isinstance(values.get('date'), str):
            date = fields.datetime.strptime(
                values.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ')
            values['date'] = date.strftime('%Y-%m-%d %H:%M:%S')
        if values.get('partner_phone'):
            array = re.findall(r'[0-9]+', values.get('partner_phone'))
            phone_number = ''
            for rec in array:
                phone_number += rec
            if len(phone_number) > 10:
                number = len(phone_number) - 10
                phone_number = phone_number[number:]
            self._cr.execute("""SELECT id FROM  res_partner where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text ilike %s limit 1""", (str(
                "%" + phone_number + "%"),))
            rec = self._cr.fetchall()
            partner_id = False
            if rec:
                partner_id = rec[0][0]
            if partner_id:
                values.update({'partner_id': partner_id})
        if values.get('crm_phonecall_about_id') and values.get('partner_id'):
            project_ids = self.env['project.project'].search([
                (
                    'phonecall_about_id',
                    '=',
                    int(values.get('crm_phonecall_about_id'))
                )], limit=1)
            if project_ids:
                project = self.env['project.project'].browse(
                    project_ids[0])
                partner = self.env['res.partner'].browse(
                    int(values.get('partner_id'))
                )
                task_vals = {
                    'name': str(project.phonecall_about_id.name) + ': ' + str(
                        partner.name),
                    'project_id': project.id,
                    'description': values.get('description') or '',
                    'user_id': self._uid,
                    'partner_id': partner.id,
                }
                self.env['project.task'].create(task_vals)
        return super(CrmPhonecall, self).create(values)

    def write(self, values):
        if values.get('partner_phone'):
            array = re.findall(r'[0-9]+', values.get('partner_phone'))
            phone_number = ''
            for rec in array:
                phone_number += rec
            if len(phone_number) > 10:
                number = len(phone_number) - 10
                phone_number = phone_number[number:]
            self._cr.execute("""SELECT id FROM  res_partner where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text ilike %s limit 1""", (str(
                "%" + phone_number + "%"),))
            rec = self._cr.fetchall()
            partner_id = False
            if rec:
                partner_id = rec[0][0]
            if partner_id:
                values.update({'partner_id': partner_id})
        return super(CrmPhonecall, self).write(values)

    def _check_reschedule_call(self):
        phonecall_ids = self.search(
            [
                (
                    'date',
                    '>=',
                    fields.Datetime.to_string(
                        (datetime.now() + timedelta(days=1)).replace(
                            hour=00, minute=00, second=00)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)),
                (
                    'date',
                    '<=',
                    fields.Datetime.to_string(
                        (datetime.now() + timedelta(days=1)).replace(
                            hour=23, minute=59, second=59)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                ),
                ('state', '=', 'open')
            ])
        if phonecall_ids:
            for phonecall in phonecall_ids:
                template_id = self.env['ir.model.data'].get_object_reference(
                    'crm_voip',
                    'email_check_reschedule')[1]
                self.env['mail.template'].send_mail(
                    template_id, phonecall.id, force_send=True)
        return True

    def check_crm_phonecall(self):
        phonecall_list = []
        phonecall_ids = self.search([
            (
                'user_id',
                '=',
                self._uid
            ),
            (
                'date',
                '>=',
                fields.Datetime.to_string(
                    (datetime.now() + timedelta(days=1)).replace(
                        hour=00, minute=00, second=00)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)),
            (
                'date',
                '<=',
                fields.Datetime.to_string(
                    (datetime.now() + timedelta(days=1)).replace(
                        hour=23, minute=59, second=59)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
            )
        ])
        if phonecall_ids:
            for phonecall in phonecall_ids:
                if phonecall.name or phonecall.partner_phone:
                    message = \
                        phonecall.name \
                        or '' + '\n' + phonecall.partner_phone or ''
                phonecall_list.append({
                    'phonecall_id': phonecall.id,
                    'message': message
                })
        return phonecall_list

    def schedule_another_phonecall(
            self, schedule_time, call_summary, user_id=False, team_id=False,
            categ_id=False):
        model_data = self.env['ir.model.data']
        phonecall_dict = {}
        if not categ_id:
            try:
                res_id = model_data._get_id('crm', 'categ_phone2')
                categ_id = model_data.browse(res_id).res_id
            except ValueError:
                pass
        for call in self:
            if call.state != "done":
                call.state = "cancel"
                call.in_queue = False
            if not team_id:
                team_id = call.team_id and call.team_id.id or False
            if not user_id:
                user_id = call.user_id and call.user_id.id or False
            if not schedule_time:
                schedule_time = call.date
            vals = {
                'name': call_summary,
                'user_id': user_id or False,
                'categ_id': categ_id or False,
                'description': False,
                'date': schedule_time,
                'team_id': team_id or False,
                'partner_id': call.partner_id and call.partner_id.id or False,
                'partner_phone': call.partner_phone,
                'partner_mobile': call.partner_mobile,
                'priority': call.priority,
                'opportunity_id':
                    call.opportunity_id and call.opportunity_id.id or False,
            }
            new_id = self.create(vals)
            phonecall_dict[call.id] = new_id
        return phonecall_dict

    @api.model
    def get_partner_name(self, number):
        array = re.findall(r'[0-9]+', number)
        phone_number = ''
        for rec in array:
            phone_number += rec
        if len(phone_number) > 10:
            number = len(phone_number) - 10
            phone_number = phone_number[number:]
        self._cr.execute("""SELECT id FROM  res_partner where NULLIF(regexp_replace(phone, '\D','','g'), '')::numeric::text ilike %s""", (str(
            "%" + phone_number + "%"),))
        rec = self._cr.fetchall()
        rec_li = []
        if rec:
            for rec_id in rec:
                rec_li.append(rec_id[0])
        rec = self.env['res.partner'].search_read(
            [('id', 'in', rec_li)], ['name', 'phone'])
        return rec

    def on_change_opportunity(self, opportunity_id):
        values = {}
        if opportunity_id:
            opportunity = self.env['crm.lead'].browse(opportunity_id)
            values = {
                'team_id':
                    opportunity.team_id and opportunity.team_id.id or False,
                'partner_phone': opportunity.phone,
                'partner_mobile': opportunity.mobile,
                'partner_id':
                    opportunity.partner_id and opportunity.partner_id.id or
                    False,
            }
        return {'value': values}

    def redirect_phonecall_view(self, phonecall_id):
        model_data = self.env['ir.model.data']
        tree_view = model_data.get_object_reference(
            'crm', 'crm_case_phone_tree_view')
        form_view = model_data.get_object_reference(
            'crm', 'crm_case_phone_form_view')
        search_view = model_data.get_object_reference(
            'crm', 'view_crm_case_phonecalls_filter')
        value = {
            'name': _('Phone Call'),
            'view_mode': 'tree,form',
            'res_model': 'crm.phonecall',
            'res_id': int(phonecall_id),
            'views': [(form_view and form_view[1] or False, 'form'),
                      (tree_view and tree_view[1] or False, 'tree'),
                      (False, 'calendar')],
            'type': 'ir.actions.act_window',
            'search_view_id': search_view and search_view[1] or False,
        }
        return value

    def init_call(self):
        self.start_time = int(time.time())

    def hangup_call(self):
        stop_time = int(time.time())
        duration = float(stop_time - self.start_time)
        self.duration = float(duration / 60.0)
        self.state = "done"
        return {"duration": self.duration}

    def rejected_call(self):
        self.state = "pending"

    def remove_from_queue(self):
        self.in_queue = False
        if (self.state == "open"):
            self.state = "cancel"
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    def get_info(self):
        type = dict(
            self.fields_get(
                allfields=['type'])['type']['selection'])[self.type]
        return {
            "id": self.id,
            "description": self.description,
            "name": self.name,
            "state": self.state,
            "type": type,
            "date": self.date,
            "duration": self.duration,
            "partner_id": self.partner_id.id,
            "partner_name": self.partner_id.name,
            "partner_image_small": self.partner_id.image_128,
            "partner_email": self.partner_id.email,
            "partner_title": self.partner_id.title.name,
            "partner_phone":
                self.partner_phone or self.partner_mobile or
                self.opportunity_id.phone or
                self.opportunity_id.partner_id.phone or
                self.opportunity_id.partner_id.mobile or False,
            "opportunity_name": self.opportunity_id.name,
            "opportunity_id": self.opportunity_id.id,
            "opportunity_priority": self.opportunity_id.priority,
            "opportunity_title_action": self.opportunity_id.title_action,
            "opportunity_date_action": self.opportunity_id.date_action,
            "opportunity_company_currency":
                self.opportunity_id.company_currency.id,
            "max_priority":
                self.opportunity_id._fields['priority'].selection[-1][0]}

    @api.model
    def get_list(self):
        date_today = datetime.now()
        return {"phonecalls": self.search([
            ('in_queue', '=', True),
            ('user_id', '=', self.env.user[0].id),
            ('date', '<=', date_today.strftime(DEFAULT_SERVER_DATE_FORMAT))],
            order='sequence,id')
            .get_info()}


class CrmCallActivity(models.Model):
    _name = 'crm.call.activity'

    name = fields.Char('Reason')
    type = fields.Selection(
        [('in_bound', 'In Bound'), ('out_bound', 'Out Bound')],
        string='Type'
    )
    call_type = fields.Char('Type')
    leg_type = fields.Char('leg Type')
    from_number = fields.Char('From number')
    to_number = fields.Char('To number')
    act_date = fields.Datetime('Activity Date')
    from_user = fields.Many2one('res.users', 'Transfer From')
    to_user = fields.Many2one('res.users', 'Transfer To')
    crm_phonecall_id = fields.Many2one('crm.phonecall', 'Phonecall')


class InOutTaggedDocumented(models.Model):
    _name = "in.out.tagged.documented"

    name = fields.Char('Name')


class CrmLead(models.Model):
    _inherit = "crm.lead"
    in_call_center_queue = fields.Boolean(
        "Is in the Call Queue", compute='compute_is_call_center')

    def compute_is_call_center(self):
        phonecall = self.env['crm.phonecall'].search(
            [('in_queue', '=', True),
             ('state', '!=', 'done'), ('user_id', '=', self.env.user[0].id)])
        if phonecall:
            self.in_call_center_queue = True
        else:
            self.in_call_center_queue = False

    def create_call_in_queue(self):
        for opp in self:
            self.env['crm.phonecall'].create({
                'name': opp.name,
                'duration': 0,
                'user_id': self.env.user[0].id,
                'opportunity_id': opp.id,
                'partner_id': opp.partner_id.id,
                'state': 'open',
                'partner_phone': opp.phone or opp.partner_id.phone,
                'partner_mobile': opp.partner_id.mobile,
                'in_queue': True,
                'type': 'out_bound',
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    def create_custom_call_center_call(self):
        phonecall = self.env['crm.phonecall'].create({
            'name': self.name,
            'duration': 0,
            'user_id': self.env.user[0].id,
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'state': 'open',
            'partner_phone': self.phone or self.partner_id.phone,
            'in_queue': True,
            'type': 'out_bound',
        })
        return {
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.custom.phonecall.wizard",
            'multi': "True",
            'target': 'new',
            'context': {'phonecall_id': phonecall.id,
                        'default_name': phonecall.name,
                        'default_partner_id': phonecall.partner_id.id,
                        'default_user_id': self.env.user[0].id,
                        },
            'views': [[False, 'form']],
        }

    def delete_call_center_call(self):
        phonecall = self.env['crm.phonecall'].search(
            [('opportunity_id', '=', self.id), ('in_queue', '=', True),
             ('user_id', '=', self.env.user[0].id)])
        phonecall.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    def log_new_phonecall(self):
        phonecall = self.env['crm.phonecall'].create({
            'name': self.name,
            'user_id': self.env.user[0].id,
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'state': 'done',
            'partner_phone': self.phone or self.partner_id.phone,
            'partner_mobile': self.partner_id.mobile,
            'in_queue': False,
            'type': 'out_bound',
        })
        return {
            'name': _('Log a call'),
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.phonecall.log.wizard",
            'multi': "True",
            'target': 'new',
            'context': {
                'phonecall_id': phonecall.id,
                'default_opportunity_id': phonecall.opportunity_id.id,
                'default_name': phonecall.name,
                'default_duration': phonecall.duration,
                'default_description': phonecall.description,
                'default_opportunity_name': phonecall.opportunity_id.name,
                'default_opportunity_planned_revenue':
                    phonecall.opportunity_id.planned_revenue,
                'default_opportunity_title_action':
                    phonecall.opportunity_id.title_action,
                'default_opportunity_date_action':
                    phonecall.opportunity_id.date_action,
                'default_opportunity_probability':
                    phonecall.opportunity_id.probability,
                'default_partner_id': phonecall.partner_id.id,
                'default_partner_name': phonecall.partner_id.name,
                'default_partner_email': phonecall.partner_id.email,
                'default_partner_phone':
                    phonecall.opportunity_id.phone or
                    phonecall.partner_id.phone,
                'default_partner_image_small':
                    phonecall.partner_id.image_128
            },
            'default_show_duration': self._context.get(
                'default_show_duration'),
            'views': [[False, 'form']],
            'flags': {
                'headless': True,
            },
        }


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_phone_count(self):
        for partner in self:
            partner.phone_count = len(partner.ph_log_ids)

    ph_log_ids = fields.One2many('crm.phonecall', 'partner_id',
                                 'Phonecall Log',
                                 domain=['|', ('type', '=', 'in_bound'),
                                         ('type', '=', 'out_bound')])
    msg_log_ids = fields.One2many('crm.phonecall', 'partner_id', 'Message Log',
                                  domain=[('type', '=', 'sent')])
    phone_count = fields.Integer(compute='_get_phone_count', string="Phones",
                                 multi='opp_meet')

    def create_call_in_queue(self, number):
        phonecall = self.env['crm.phonecall'].create({
            'name': 'Call for ' + self.name,
            'duration': 0,
            'user_id': self.env.user[0].id,
            'partner_id': self.id,
            'state': 'open',
            'partner_phone': number,
            'in_queue': True,
            'type': 'out_bound',
        })
        return phonecall.id


class CrmPhonecallLogWizard(models.TransientModel):
    _name = 'crm.phonecall.log.wizard'

    description = fields.Text('Description')
    name = fields.Char(readonly=True)
    type = fields.Selection(
        [('in_bound', 'In Bound'), ('out_bound', 'Out Bound'),
         ], string='Type', default='out_bound')
    tag_ids = fields.Many2many('in.out.tagged.documented',
                               'rel_tagged_documented_log',
                               'tagged_documented_log_id', 'phoncall_log_id',
                               'Tag')
    opportunity_id = fields.Integer(readonly=True)
    opportunity_name = fields.Char(readonly=True)
    opportunity_planned_revenue = fields.Char(readonly=True)
    opportunity_title_action = fields.Char('Next Action')
    opportunity_date_action = fields.Date('Next Action Date')
    opportunity_probability = fields.Float(readonly=True)
    partner_id = fields.Integer(readonly=True)
    partner_name = fields.Char(readonly=True)
    partner_email = fields.Char(readonly=True)
    partner_phone = fields.Char(readonly=True)
    partner_image_small = fields.Char(readonly=True)
    duration = fields.Char('Duration', readonly=True)
    reschedule_option = fields.Selection([
        ('no_reschedule', "Don't Reschedule"),
        ('1d', 'Tomorrow'),
        ('7d', 'In 1 Week'),
        ('15d', 'In 15 Day'),
        ('2m', 'In 2 Months'),
        ('custom', 'Specific Date')
    ], 'Schedule A New Call', required=True, default="no_reschedule")
    reschedule_date = fields.Datetime(
        'Specific Date',
        default=lambda *a: datetime.now() + timedelta(hours=2))
    next_activity_id = fields.Many2one("crm.activity", "Next Activity")
    new_title_action = fields.Char('Next Action')
    new_date_action = fields.Date()
    show_duration = fields.Boolean()
    custom_duration = fields.Float(default=0)
    in_automatic_mode = fields.Boolean()

    def schedule_again(self):
        new_phonecall = self.env['crm.phonecall'].create({
            'name': self.description,
            'duration': 0,
            'user_id': self.env.user[0].id,
            'opportunity_id': self.opportunity_id,
            'partner_id': self.partner_id,
            'type': self.type,
            'tag_ids': [(6, 0, self.tag_ids.ids)] or '',
            'state': 'open',
            'partner_phone': self.partner_phone,
            'in_queue': True,
        })
        if self.reschedule_option == "7d":
            new_phonecall.date = datetime.now() + timedelta(weeks=1)
        elif self.reschedule_option == "1d":
            new_phonecall.date = datetime.now() + timedelta(days=1)
        elif self.reschedule_option == "15d":
            new_phonecall.date = datetime.now() + timedelta(days=15)
        elif self.reschedule_option == "2m":
            new_phonecall.date = datetime.now() + timedelta(weeks=8)
        elif self.reschedule_option == "custom":
            new_phonecall.date = self.reschedule_date

    def modify_phonecall(self, phonecall):
        phonecall.description = self.description
        if self.opportunity_id:
            opportunity = self.env['crm.lead'].browse(self.opportunity_id)
            # if self.next_activity_id:
            #     opportunity.next_activity_id = self.next_activity_id
            #     opportunity.title_action = self.new_title_action
            #     opportunity.date_action = self.new_date_action
            if self.show_duration:
                mins = int(self.custom_duration)
                sec = (self.custom_duration - mins) * 0.6
                sec = '%.2f' % sec
                time = str(mins) + ":" + sec[-2:]
                message = "Call " + time + " min(s)"
                phonecall.duration = self.custom_duration
            else:
                message = "Call " + self.duration + " min(s)"
            if phonecall.description:
                message += " about " + phonecall.description
            opportunity.message_post(message)
        if self.reschedule_option != "no_reschedule":
            self.schedule_again()

    def save(self):
        phonecall = self.env['crm.phonecall'].browse(
            self._context.get('phonecall_id'))
        self.modify_phonecall(phonecall)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
            'params': {'in_automatic_mode': self.in_automatic_mode},
        }

    def save_go_opportunity(self):
        phonecall = self.env['crm.phonecall'].browse(
            self._context.get('phonecall_id'))
        self.modify_phonecall(phonecall)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
            'params': {'go_to_opp': True,
                       'opportunity_id': self.opportunity_id,
                       'in_automatic_mode': self.in_automatic_mode},
        }


class CrmCustomPhonecallWizard(models.TransientModel):
    _name = 'crm.custom.phonecall.wizard'

    name = fields.Char('Call summary', required=True)
    user_id = fields.Many2one('res.users', "Assign To")
    date = fields.Datetime('Date', required=True,
                           default=lambda *a: datetime.now())
    partner_id = fields.Many2one('res.partner', "Partner")

    def action_schedule(self):
        phonecall = self.env['crm.phonecall'].browse(
            self._context.get('phonecall_id'))
        phonecall.name = self.name
        phonecall.date = self.date
        phonecall.partner_id = self.partner_id
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }


class CrmPhonecallTransferWizard(models.TransientModel):
    _name = 'crm.phonecall.transfer.wizard'

    transfer_number = fields.Char('transfer To')
    transfer_choice = fields.Selection(
        selection=[('physical', 'transfer to your external phone'),
                   ('extern', 'transfer to another External Phone')],
        default='physical', required=True)

    def save(self):
        if self.transfer_choice == 'extern':
            action = {
                'type': 'ir.actions.client',
                'tag': 'transfer_call',
                'params': {'number': self.transfer_number},
            }
        else:
            if self.env.user[0].sip_external_phone:
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'transfer_call',
                    'params': {'number': self.env.user[0].sip_external_phone},
                }
            else:
                action = {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "Wrong configuration for the call."
                            "There is no external phone number configured"),
                    },
                }
        return action


class CrmPhonecallReport(models.Model):
    _name = "crm.phonecall.report"
    _description = "Phone Calls by user and team"
    _auto = False

    user_id = fields.Many2one('res.users', 'Responsible', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Contact', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    duration = fields.Float('Duration', digits=(16, 2), group_operator="avg",
                            readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', index=True,
                              help="Sales team to which Case belongs to.")
    categ_id = fields.Many2one('crm.phonecall.category', 'Category')
    state = fields.Selection([
        ('pending', 'Not Held'),
        ('cancel', 'Cancelled'),
        ('open', 'To Do'),
        ('done', 'Held')
    ], 'Status', readonly=True)
    date = fields.Datetime('Date', readonly=True, index=True)
    nbr = fields.Integer('# of Cases', readonly=True)

    def init(self):
        """ Phone Calls By User And Team
            @param cr: the current row, from the database cursor,
        """
        tools.drop_view_if_exists(self._cr, 'crm_phonecall_report')
        self._cr.execute("""
            create or replace view crm_phonecall_report as (
                select
                    id,
                    c.state,
                    c.user_id,
                    c.team_id,
                    c.categ_id,
                    c.partner_id,
                    c.duration,
                    c.company_id,
                    c.priority,
                    1 as nbr,
                    c.date
                from
                    crm_phonecall c
                where
                    c.state = 'done'
            )""")


class CrmPhonecall2phonecall(models.TransientModel):
    _name = "crm.phonecall2phonecall"

    date = fields.Datetime('Date', required=True)
    name = fields.Char('Call summary', required=True, index=True)
    user_id = fields.Many2one('res.users', "Assign To")
    contact_name = fields.Char('Contact')
    phone = fields.Char('Phone')
    categ_id = fields.Many2one('crm.phonecall.category', 'Category')
    team_id = fields.Many2one('crm.team', 'Sales Team')
    partner_id = fields.Many2one('res.partner', "Partner")
    note = fields.Text('Note')

    def action_cancel(self):
        """
        Closes Phonecall to Phonecall form
        """
        return {'type': 'ir.actions.act_window_close'}

    def action_schedule(self):
        phonecall = self.env['crm.phonecall']
        phonecall_ids = self._context and self._context.get('active_ids') or []
        for this in self:
            phonecall.schedule_another_phonecall(
                phonecall_ids, this.date, this.name,
                this.user_id and this.user_id.id or False,
                this.team_id and this.team_id.id or False,
                this.categ_id and this.categ_id.id or False)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    @api.model
    def default_get(self, fields):
        """ This function gets default values """
        res = super(CrmPhonecall2phonecall, self).default_get(fields)
        context = self._context
        active_id = context and context.get('active_id', False) or False
        if active_id:
            phonecall = self.env['crm.phonecall'].browse(active_id)
            categ_id = False
            data_obj = self.env['ir.model.data']
            try:
                res_id = data_obj._get_id('crm', 'categ_phone2')
                categ_id = data_obj.browse(res_id).res_id
            except ValueError:
                pass

            if 'name' in fields:
                res.update({'name': phonecall.name})
            if 'user_id' in fields:
                res.update({
                    'user_id':
                        phonecall.user_id and phonecall.user_id.id or False
                })
            if 'date' in fields:
                res.update({'date': False})
            if 'team_id' in fields:
                res.update({
                    'team_id':
                        phonecall.team_id and phonecall.team_id.id or False})
            if 'categ_id' in fields:
                res.update({'categ_id': categ_id})
            if 'partner_id' in fields:
                res.update({
                    'partner_id':
                        phonecall.partner_id and phonecall.partner_id.id or
                        False})
        return res


class CrmPhonecallCategory(models.Model):
    _name = "crm.phonecall.category"
    _description = "Category of phone call"

    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    def downlaod_file(self):
        for doc_id in self:
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true&filename=%s' % (
                        doc_id.id, doc_id.name),
                'target': 'new',
            }
