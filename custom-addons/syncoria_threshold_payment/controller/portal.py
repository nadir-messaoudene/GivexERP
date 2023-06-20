# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request

class InheritPortalAccount(PortalAccount):
    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices', download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        #Threshold
        over_threshold = False
        PayAcq = request.env['payment.acquirer']
        payacq_obj = PayAcq.sudo().search([('apply_threshold_website_portal', '=', True)])
        if payacq_obj.threshold_value < values['invoice'].amount_total:
            over_threshold = True
        values['over_threshold'] = over_threshold
        return request.render("account.portal_invoice_page", values)
