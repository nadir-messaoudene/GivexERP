# -*- coding: utf-8 -*-
# from odoo import http


# class L10nMxLoggerSnd(http.Controller):
#     @http.route('/l10n_mx_logger_snd/l10n_mx_logger_snd/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_mx_logger_snd/l10n_mx_logger_snd/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_mx_logger_snd.listing', {
#             'root': '/l10n_mx_logger_snd/l10n_mx_logger_snd',
#             'objects': http.request.env['l10n_mx_logger_snd.l10n_mx_logger_snd'].search([]),
#         })

#     @http.route('/l10n_mx_logger_snd/l10n_mx_logger_snd/objects/<model("l10n_mx_logger_snd.l10n_mx_logger_snd"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_mx_logger_snd.object', {
#             'object': obj
#         })
