# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools, _



class CrmActivity(models.Model):
    _name = 'crm.activity'
    _description = 'Crm Activity'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    
