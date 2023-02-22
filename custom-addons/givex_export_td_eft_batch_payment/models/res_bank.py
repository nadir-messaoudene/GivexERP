from odoo import models


class Bank(models.Model):
    _inherit = "res.bank"
    _description = "Bank"


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"
    _description = "Bank Accounts"
