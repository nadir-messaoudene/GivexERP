# Copyright 2020, Vauxoo, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.exceptions import UserError
from odoo import fields, models, api, _


def assert_xunnel_token(function):
    """Raises an user error whenever the user
    tries to manual update either providers or invoices
    without having any Xunnel Token registered in its company.
    """
    def wraper(self):
        if not self.company_id.xunnel_token:
            raise UserError(_(
                "Your company doesn't have a Xunnel Token "
                "established. Make sure you have saved your"
                " configuration changes before trying manual sync."))
        return function(self)
    return wraper

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_mx_edi_fuel_code_sat_ids = fields.Many2many(
        'l10n_mx_edi.product.sat.code', 'SAT fuel codes', readonly=False,
        related='company_id.l10n_mx_edi_fuel_code_sat_ids')
    xunnel_token = fields.Char(
        related='company_id.xunnel_token',
        help="Key-like text for authentication in controllers.",
        readonly=False)
    # xunnel_testing = fields.Boolean(
    #     help="Use Xunnel server testing?",
    #     related='company_id.xunnel_testing',
    #     readonly=False)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.company_id
        res.update(
            xunnel_token=company.xunnel_token,
            # xunnel_testing=company.xunnel_testing
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        company = self.company_id
        company.write({
            'xunnel_token': self.xunnel_token,
            # 'xunnel_testing': self.xunnel_testing
        })
        return res

    @assert_xunnel_token
    def sync_xunnel_providers(self):
        status, response = self.company_id._sync_xunnel_providers()
        if not status:
            error = _(
                "An error has occurred while synchronizing your banks. %s")
            raise UserError(error % response)
        message = _(
            "Success! %s banks have been synchronized.") % len(response)
        return {
            'type': 'ir.actions.client',
            'tag': 'account_xunnel.syncrhonized_accounts',
            'name': _('Xunnel response.'),
            'target': 'new',
            'message': message,
            'message_class': 'success',
        }
