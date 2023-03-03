# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, fields, api


class Stock_Move(models.Model):
    _inherit = 'stock.move'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=False)

    def _action_done(self, cancel_backorder=False):
        res = super(Stock_Move, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if move.inv_backdated:
                move.write({'date': move.inv_backdated})
                move.move_line_ids.write({'date': move.inv_backdated,
                                          'origin': move.origin})
        return res


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=False)
    backdated_remark = fields.Char(string="Notes", copy=False)

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super(stock_quant, self)._get_inventory_move_values(qty=qty, location_id=location_id, location_dest_id=location_dest_id, out=out)
        if self.inv_backdated:
            res.update({'inv_backdated': self.inv_backdated,
                        'date_deadline': self.inv_backdated,
                        'origin': self.backdated_remark})
        return res

    def _apply_inventory(self):
        for inventories in self.filtered(lambda l:l.inv_backdated):
            inventories.accounting_date = inventories.inv_backdated
        res = super(stock_quant, self)._apply_inventory()
        for inventories in self.filtered(lambda l:l.inv_backdated):
            inventories.write({'inv_backdated': False, 'backdated_remark': False})
        return res

    @api.model
    def _get_inventory_fields_create(self):
        res = super(stock_quant,self)._get_inventory_fields_create()
        res += ['inv_backdated','backdated_remark']
        return res

    @api.model
    def _get_inventory_fields_write(self):
        res = super(stock_quant,self)._get_inventory_fields_write()
        res += ['inv_backdated','backdated_remark']
        return res


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