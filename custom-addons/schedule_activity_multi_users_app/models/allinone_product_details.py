# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderInherit(models.Model):
	_inherit = 'mail.activity'

	assign_multi = fields.Many2many('res.users', 
		string = 'Assign Multi Users')
	state_process = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'Progress'),
        ('done', 'Done')], string="Delay units",
        default='draft')


	def action_close_dialog(self):
		res = super(SaleOrderInherit,self).action_close_dialog()

		if self.assign_multi:
			for order in self.assign_multi:
				if not self.activity_type_id.category in ('meeting'):
					if self.state_process == 'draft':
						self.create({
							'activity_type_id':self.activity_type_id.id,
							'date_deadline':self.date_deadline,
							'assign_multi':self.assign_multi,
							'user_id':order.id,
							'note':self.note,
							'summary':self.summary,
							'state_process':'progress'})

					elif self.state_process == 'progress':
						result = self.env['mail.activity'].browse(self.id)

						result.write({
							'activity_type_id':self.activity_type_id.id,
							'date_deadline':self.date_deadline,
							'assign_multi':self.assign_multi,
							'user_id':order.id,
							'note':self.note,
							'summary':self.summary})

				else:
					if self.state_process == 'draft':
						self.create({
						'activity_type_id':self.activity_type_id.id,
						'user_id':order.id,
						'assign_multi':self.assign_multi,
						'summary':self.summary,
						'state_process':'progress'})

					elif self.state_process == 'progress':
						result = self.env['mail.activity'].browse(self.id)

						result.write({
						'activity_type_id':self.activity_type_id.id,
						'user_id':order.id,
						'assign_multi':self.assign_multi,
						'summary':self.summary})

		return res


	def _check_access_assignation(self):
		for activity in self:
			model = self.env[activity.res_model].with_user(
				activity.user_id)


