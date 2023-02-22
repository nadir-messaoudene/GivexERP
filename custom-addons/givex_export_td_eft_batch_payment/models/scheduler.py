from odoo import api, models


class FilenameSequenceReset(models.Model):
    _name = 'filename.sequence.reset'
    _description = "Fine name sequence reset scheduler"

    @api.model
    def _reset_sequence(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'td.outbound.batch.payment')])
        if sequence and sequence.number_next >= 9999:
            sequence.sudo().write({'number_next': 1})
