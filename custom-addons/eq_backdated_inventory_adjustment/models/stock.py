# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, fields, api


class Stock_Move(models.Model):
    _inherit = 'stock.move'

    def _action_done(self,cancel_backorder=False):
        res = super(Stock_Move, self)._action_done(cancel_backorder)
        for each_move in res:
            if each_move.inventory_id and each_move.inventory_id.is_backdated_inv:
                each_move.write(
                    {'date':each_move.inventory_id.inv_backdated or fields.Datetime.now(),
                    'date_expected':each_move.inventory_id.inv_backdated or fields.Datetime.now(),
                    'note':each_move.inventory_id.backdated_remark, 'origin':each_move.inventory_id.backdated_remark})
                each_move.move_line_ids.write(
                    {'date':each_move.inventory_id.inv_backdated or fields.Datetime.now(),
                    'origin':each_move.inventory_id.backdated_remark})
        return res


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    is_backdated_inv = fields.Boolean(string="Is Backdated Inventory?",copy=False)
    inv_backdated = fields.Date(string="Inventory Backdate",copy=False)
    backdated_remark = fields.Char(string="Notes",copy=False)

    def post_inventory(self):
        for inventory in self:
            date = inventory.accounting_date or inventory.date
            if inventory.is_backdated_inv:
                date = inventory.inv_backdated
        return super(stock_inventory, inventory.with_context(force_period_date=date)).post_inventory()


class stock_valuation_layer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(stock_valuation_layer, self).create(vals_list)
        if self._context.get('force_period_date'):
            for each_rec in res:
                self.env.cr.execute("update stock_valuation_layer set create_date = %s where id = %s", (self._context.get('force_period_date'), each_rec.id))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: