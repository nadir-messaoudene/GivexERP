# -*- coding: utf-8 -*-
# Part of Givex. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class Project(models.Model):
    _inherit = "project.project"

class Task(models.Model):
    _inherit = "project.task"
