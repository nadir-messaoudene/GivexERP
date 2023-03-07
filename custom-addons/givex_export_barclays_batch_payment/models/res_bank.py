from odoo import fields, models

class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"
    _description = "Bank Accounts"

    sort_code = fields.Char(string="Sort-Code")
    barclays_account_type = fields.Char(string="Destination Account Type")
    bacs_code = fields.Char(string="Bacs-Code")
    free_format = fields.Char(string="Free-Format")
    originator_name = fields.Char(string="Originator-Name")
