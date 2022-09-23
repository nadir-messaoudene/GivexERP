# -*- coding: utf-8 -*-
# from odoo import http


# class ReportInvoice(http.Controller):
#     @http.route('/report_invoice/report_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_invoice/report_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_invoice.listing', {
#             'root': '/report_invoice/report_invoice',
#             'objects': http.request.env['givex_esi_report.report_invoice'].search([]),
#         })

#     @http.route('/report_invoice/report_invoice/objects/<model("givex_esi_report.report_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_invoice.object', {
#             'object': obj
#         })
