# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class ProductsController(http.Controller):

    # adding stock check option in portal
    @http.route('/my/products_on_hand', type='http', auth="user", website=True)
    def portal_products(self, **kw):
        partner = request.env['res.users'].browse(request.uid).partner_id
        partner_ids = []
        if partner:
            partner_ids.append(partner.id)
            if partner.parent_id:
                partner_ids.append(partner.parent_id.id)
        # move_line = request.env['stock.move.line'].sudo().read_group([('picking_id.partner_id', '=', partner.id)], ['product_id:count'], ['product_uom_id', 'qty_done', 'company_id'], lazy=False, orderby='qty_done asc')
        # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        move_line = request.env['stock.move.line'].sudo().search([('picking_id.partner_id', 'in', partner_ids)])
        print("move_line >>>>>>>>>>>>>>>>>>", move_line, len(move_line))
        move_line_list_by_product = []
        move_line_list_by_product_company = []
        # move_line.filtered(lambda ml: ml.product_id == product for product in )
        for product in move_line.mapped('product_id'):
            lines = move_line.filtered(lambda ml: ml.product_id == product)
            if lines:
                move_line_list_by_product.append(lines)
        for company in move_line.mapped('company_id'):
            for mll in move_line_list_by_product:
                lines_list = mll.filtered(lambda ml: ml.company_id == company)
                if lines_list:
                    move_line_list_by_product_company.append(lines_list)

            # lines = move_line.filtered(lambda ml: ml.product_id == product)
            # if lines:
            #     move_line_list.append(lines)
        print("move_line_list_by_product >>>>>>>>>>>>>>>>", move_line_list_by_product, len(move_line_list_by_product))
        print("move_line_list_by_product_company >>>>>>>>>>>>>>>>", move_line_list_by_product_company, len(move_line_list_by_product_company))
        values = {
            'products_on_hand': True,
            'move_line': move_line_list_by_product_company,
        }
        return request.render("portal_stock.portal_product_on_hand", values)

    # getting corresponding products
    # @http.route('/product/search', type='json', auth="user", website=True)
    # def search_product(self, **kw, ):
    #     product = kw.get('name')
    #     if product:
    #         res = request.env['product.product'].sudo().search_read(
    #             [('name', 'ilike', product), ('is_published', '=', True)])
    #         return res
    #     else:
    #         return False
