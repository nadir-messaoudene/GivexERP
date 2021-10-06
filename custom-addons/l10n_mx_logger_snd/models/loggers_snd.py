# -*- coding: utf-8 -*-
import logging
import base64
from itertools import groupby

from odoo import models, fields, api, tools, _
from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit


_logger = logging.getLogger(__name__)

# class PACSWMixin(models.AbstractModel):
#     _inherit = 'l10n_mx_edi.pac.sw.mixin'
#
#     def _l10n_mx_edi_sw_sign(self, pac_info):
#         _logger.warning('SND SAYS: self in _l10n_mx_edi_sw_sign contains {} at start of function'.format(self.l10n_mx_edi_cfdi))
#         token, req_e = self._l10n_mx_edi_sw_token(pac_info)
#         if not token:
#             self.l10n_mx_edi_log_error(
#                 _("Token could not be obtained %s") % req_e)
#             return
#         url = pac_info['url']
#         _logger.warning('SND SAYS: self in _l10n_mx_edi_sw_sign contains {} before rec loop'.format(self.l10n_mx_edi_cfdi))
#         for rec in self:
#             xml = rec.l10n_mx_edi_cfdi.decode('UTF-8')
#             boundary = self._l10n_mx_edi_sw_boundary()
#             payload = """--%(boundary)s
#     Content-Type: text/xml
#     Content-Transfer-Encoding: binary
#     Content-Disposition: form-data; name="xml"; filename="xml"
#
#     %(xml)s
#     --%(boundary)s--
#     """ % {'boundary': boundary, 'xml': xml}
#             headers = {
#                 'Authorization': "bearer " + token,
#                 'Content-Type': ('multipart/form-data; '
#                                  'boundary="%s"') % boundary,
#             }
#             payload = payload.replace('\n', '\r\n').encode('UTF-8')
#             response_json = self._l10n_mx_edi_sw_post(
#                 url, headers, payload=payload)
#             code = response_json.get('message')
#             msg = response_json.get('messageDetail')
#             try:
#                 xml_signed = response_json['data']['cfdi']
#             except (KeyError, TypeError):
#                 xml_signed = None
#             rec._l10n_mx_edi_post_sign_process(
#                 xml_signed.encode('utf-8') if xml_signed else None,
#                 code, msg)
#
# class AccountMove(models.Model):
#     _name = 'account.move'
#     _inherit = ['account.move', 'l10n_mx_edi.pac.sw.mixin']
#
#     @run_after_commit
#     def _l10n_mx_edi_call_service(self, service_type):
#         '''Call the right method according to the pac_name, it's info returned by the '_l10n_mx_edi_%s_info' % pac_name'
#         method and the service_type passed as parameter.
#         :param service_type: sign or cancel
#         '''
#         # Regroup the invoices by company (= by pac)
#         comp_x_records = groupby(self, lambda r: r.company_id)
#         for company_id, records in comp_x_records:
#             pac_name = company_id.l10n_mx_edi_pac
#             if not pac_name:
#                 continue
#             # Get the informations about the pac
#             pac_info_func = '_l10n_mx_edi_%s_info' % pac_name
#             service_func = '_l10n_mx_edi_%s_%s' % (pac_name, service_type)
#             pac_info = getattr(self, pac_info_func)(company_id, service_type)
#             # Call the service with invoices one by one or all together according to the 'multi' value.
#             multi = pac_info.pop('multi', False)
#             if multi:
#                 # rebuild the recordset
#                 records = self.env['account.move'].search(
#                     [('id', 'in', self.ids), ('company_id', '=', company_id.id)])
#                 getattr(records, service_func)(pac_info)
#             else:
#                 for record in records:
#                     _logger.warning('SND SAYS: record in _l10n_mx_edi_call_service contains {}'.format(record))
#                     getattr(record, service_func)(pac_info)

class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'l10n_mx_edi.pac.sw.mixin']

    def _l10n_mx_edi_retry(self):
        '''Try to generate the cfdi attachment and then, sign it.
        '''
        version = self.l10n_mx_edi_get_pac_version()
        for inv in self:
            cfdi_values = inv._l10n_mx_edi_create_cfdi()
            error = cfdi_values.pop('error', None)
            cfdi = cfdi_values.pop('cfdi', None)
            if error:
                # cfdi failed to be generated
                inv.l10n_mx_edi_pac_status = 'retry'
                inv.message_post(body=error, subtype='account.mt_invoice_validated')
                _logger.error('The CFDI generated for the invoice %s is not valid: %s' % (inv.name, str(error)))
                continue
            # cfdi has been successfully generated
            inv.l10n_mx_edi_pac_status = 'to_sign'
            filename = ('%s-%s-MX-Invoice-%s.xml' % (
                inv.journal_id.code, inv.name, version.replace('.', '-'))).replace('/', '')
            ctx = self.env.context.copy()
            ctx.pop('default_type', False)
            inv.l10n_mx_edi_cfdi_name = filename
            # _logger.warning(
            #     'SND SAYS: self in _l10n_mx_edi_retry contains {} before attachment'.format(self.l10n_mx_edi_cfdi))
            attachment_id = self.env['ir.attachment'].with_context(ctx).create({
                'name': filename,
                'res_id': inv.id,
                'res_model': inv._name,
                'datas': base64.encodestring(cfdi),
                'description': 'Mexican invoice',
                })
            # if inv.l10n_mx_edi_cfdi == False:
            #     inv.l10n_mx_edi_cfdi = attachment_id.datas
            inv.message_post(
                body=_('CFDI document generated (may be not signed)'),
                attachment_ids=[attachment_id.id],
                subtype='account.mt_invoice_validated')
            if not self.l10n_mx_edi_cfdi:
                _logger.warning('SND SAYS: self in _l10n_mx_edi_retry IS EMPTY after attachment')
            else:
                _logger.warning('SND SAYS: self in _l10n_mx_edi_retry HAS CFDI after attachment')
            inv._l10n_mx_edi_sign()