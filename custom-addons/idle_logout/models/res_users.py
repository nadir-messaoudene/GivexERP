# -*- coding: utf-8 -*-

from odoo import api, http, models, tools, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    idle_timer = fields.Integer(string="Idle Timer (seconds)", default=7200)

    def idle_times(self):
        print("\n\n\n", self.idle_timer)
        return self.idle_timer

