###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from . import models
from . import controllers
# from . import tests
from odoo import _
from odoo.service import common
from odoo.exceptions import Warning
from odoo.addons.payment import reset_payment_provider
from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers



def pre_init_check(cr):
    version_info = common.exp_version()
    server_serie = version_info.get("server_serie")
    if server_serie != "13.0":
        raise Warning(_('Module support Odoo series 13.0 found {}.').format(server_serie))
    return True


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "bamboraeft")
