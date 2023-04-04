from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.osv import osv


class InheritCron(models.Model):
    _inherit = 'ir.cron'

    auto_sync_ticket = fields.Boolean('Auto Sync Tickets')


class ZendeskSupport(models.Model):
    _name = 'zendesk.autosync'
    _description = 'Autosync'
    _rec_name = "id"

    auto_sync_active = fields.Boolean('Auto Sync')
    field_name = fields.Char('Zendesk AutoSync')
    ticket_help = "If You enable it, so whenever you create or " \
                  "update ticket it will automatically sync to" \
                  " zendesk"
    zendesk_support = fields.Boolean('Activate Scheduler')
    auto_sync_ticket = fields.Boolean('Auto Sync Tickets',
                                      help=ticket_help)
    auto_contact = fields.Boolean('Sync Contact')
    auto_ticket = fields.Boolean('Sync Ticket')
    auto_message = fields.Boolean('Sync Message')
    email_id = fields.Char()
    passw = fields.Char()
    co_name = fields.Char()
    interval_number = fields.Integer(string="Interval Number")
    interval_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('work_days', 'Work Days'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Interval Unit')

    @api.onchange('auto_sync_ticket')
    def _onchange_auto_sync_ticket(self):
        for rec in self:
            if rec.auto_sync_ticket:
                rec.zendesk_support = True

    def unlink(self):
        # raise UserError(('Not allowed to delete, Just diable the scheduler by editing form.'))
        raise osv.except_osv('Deletion Not Allowed!', 'Just disable the scheduler by editing form.')

    def sync_data_scheduler(self):
        done = False
        while not done:
            try:
                scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler')])
                if not scheduler:
                    scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler'),
                                                            ('active', '=', False)])
                    scheduler.active = self.zendesk_support
                    scheduler.interval_number = self.interval_number
                    scheduler.interval_type = self.interval_unit
                    scheduler.auto_sync_ticket = self.auto_sync_ticket

                elif scheduler.active:
                    # scheduler = self.env['ir.cron'].search([('name', '=', 'Tickets Scheduler'),
                    #                                         ('active', '=', True)])
                    scheduler.active = self.zendesk_support
                    scheduler.interval_number = self.interval_number
                    scheduler.interval_type = self.interval_unit
                    scheduler.auto_sync_ticket = self.auto_sync_ticket

                self.env.cr.commit()
                done = True
            except Exception as e:
                raise (str(e))
