from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    editing = fields.Boolean(default=False)

    @api.onchange('order_line', 'order_line.price_unit', 'order_line.product_qty')
    def onchangeOrderLine(self):
        self.editing = True

    def button_confirm(self):
        self.editing = False
        return super(PurchaseOrder, self).button_confirm()

    def write(self, values):
        new_status = False
        active_id = None

        if self.env.context.get('active_id'):
            active_id = self.env.context['active_id']
        elif len(self.ids) == 1:
            active_id = self.ids[0]
        if active_id and 'state' not in values:
            purchase_order = self.env['purchase.order'].sudo().browse(active_id)
            curr_state = self.env.cr.execute("SELECT state FROM purchase_order WHERE id = {0}".format(active_id))
            if curr_state != 'purchase':
                for order in purchase_order:
                    if order.state == 'purchase' and self.editing == True:
                        new_status = True
                if new_status:
                    values['state'] = 'draft'
        return super(PurchaseOrder, self).write(values)
