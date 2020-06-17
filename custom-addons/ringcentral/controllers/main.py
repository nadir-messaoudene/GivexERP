# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class RingcentralController(http.Controller):

    @http.route('/ringcentral_credentials', type='json', auth='user')
    def ringcentral_credentials(self, **kw):
        
        company = request.env['res.company'].sudo().browse(
            kw.get('company_id'))
        return {
            'ringcentral_app_host': company.ringcentral_app_host,
            'ringcentral_app_port': company.ringcentral_app_port,
            'ringcentral_redirect_uri': company.ringcentral_redirect_uri,
            'ringcentral_server': company.ringcentral_server,
            'ringcentral_app_key': company.ringcentral_app_key,
            'ringcentral_app_secret': company.ringcentral_app_secret,
            'ringcentral_service_uri': company.ringcentral_service_uri,
        }
