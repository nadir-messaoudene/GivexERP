# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api, _

class AccountInvoiceSend(models.TransientModel):
	_inherit = 'account.invoice.send'
	_description = 'Account Invoice Send'

	template_id = fields.Many2one('mail.template', 'Use template', index=True)

	@api.model
	def default_get(self, fields):
		result = super(AccountInvoiceSend, self).default_get(fields)
		if result:
			company = self.env.user.company_id
			config_obj = self.env['res.config.settings'].search([], limit=1, order="id desc")
			result.update({ 
				'template_id' : company.invoice_template.id,
			})
			composer_id = self.env['mail.compose.message'].browse(result.get('composer_id'))
			composer_id.write({
				'template_id' : self.template_id,
			})
		return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: