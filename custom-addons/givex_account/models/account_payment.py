
import logging

from odoo import models

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_force_reset_payment(self):
        for pay in self:
            if pay.move_id:
                update_sql = """UPDATE account_move
                                        SET is_move_sent = %s,
                                            state = %s
                                        WHERE id = %s"""
                try:
                    self.env.cr.execute(update_sql, (False, 'draft', pay.move_id.id))
                    self.env.cr.commit()
                except Exception as e:
                    _logger.warning("Account move : update account move  failed. Error: %s" % e)
