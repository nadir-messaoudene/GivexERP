# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'res.partner'

    ringcentral_id = fields.Char("Ringcentral id")

    @api.model
    def ac_search_read(self, records):
        rec_message = self.search([])
        rec_message_id = rec_message.mapped('ringcentral_id')
        for rec_vals in records:
            if not rec_vals.get('id') in rec_message_id:
                vals = {
                    'ringcentral_id': rec_vals.get('id'),
                    'name': rec_vals.get('firstName'),
                    'phone': rec_vals.get('phone'),
                    'mobile': rec_vals.get('mobile')
                }
                self.create(vals)
        return rec_message_id

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        pass

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        pass


class ResUser(models.Model):
    _inherit = 'res.users'

    ringcentral_access_token = fields.Char("Ringcentral Acess Token")
