# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from codecs import BOM_UTF8
from datetime import date
from time import mktime

from lxml import etree, objectify
from odoo import _, api, fields, models
from odoo.exceptions import UserError


BOM_UTF8U = BOM_UTF8.decode('UTF-8')

class ProductSatCode(models.Model):
    """Product and UOM Codes from SAT Data.
    This code must be defined in CFDI 3.3, in each concept, and this is set
    by each product.
    Is defined a new catalog to only allow select the codes defined by the SAT
    that are load by data in the system.
    This catalog is found `here <https://goo.gl/iAUGEh>`_ in the page
    c_ClaveProdServ.

    This model also is used to define the uom code defined by the SAT
    """
    _name = 'l10n_mx_edi.product.sat.code'
    _description = "Product and UOM Codes from SAT Data"

    code = fields.Char(
        help='This value is required in CFDI version 3.3 to express the '
        'code of product or service covered by the present concept. Must be '
        'used a key from SAT catalog.', required=True)
    name = fields.Char(
        help='Name defined by SAT catalog to this product',
        required=True)
    applies_to = fields.Selection([
        ('product', 'Product'),
        ('uom', 'UoM'),
    ], required=True,
        help='Indicate if this code could be used in products or in UoM',)
    active = fields.Boolean(
        help='If this record is not active, this cannot be selected.',
        default=True)

class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_last_sync = fields.Date(string='Last Sync with Xunnel', default=lambda _: date.today())
    l10n_mx_edi_fuel_code_sat_ids = fields.Many2many(
        'l10n_mx_edi.product.sat.code', string='SAT fuel codes',
        domain=[('applies_to', '=', 'product')])

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        """Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        """
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def _sync_xunnel_documents(self):
        """Requests https://wwww.xunnel.com/ to retrive all invoices
        related to the current company and check them in the database
        to create them if they're not. After refresh xunnel_last_sync
        """
        self.ensure_one()
        if not self.vat and self.xunnel_token:
            raise UserError(_('You need to define the VAT of your company.'))
        values = dict(
            last_sync=False,
            xunnel_testing=False,
            vat=self.vat)
        if self.xunnel_last_sync:
            values.update(last_sync=mktime(self.xunnel_last_sync.timetuple()))
        response = self._xunnel('get_invoices_sat', values)
        err = response.get('error')
        if err:
            raise UserError(err)
        if response.get('response') is None:
            return True
        dates = []
        failed = 0
        created = []
        folder_id = self.env.ref('documents.documents_finance_folder')
        tag_id = self.env.ref('invoice_xunnel.without_invoice')
        for item in response.get('response'):
            xml = item.lstrip(BOM_UTF8U).encode("UTF-8")
            try:
                xml = xml.replace(b'xmlns:schemaLocation', b'xsi:schemaLocation')
                xml_obj = objectify.fromstring(xml)
            except etree.XMLSyntaxError:
                failed += 1
                continue
            xml_type = xml_obj.get('TipoDeComprobante', False)
            tags_type = self.get_tag_map(xml_type) | tag_id
            dates.append(xml_obj.get('Fecha', xml_obj.get('fecha', ' ')))
            uuid = self.l10n_mx_edi_get_tfd_etree(xml_obj).get('UUID')
            datas_fname = "%s.xml" % (uuid)
            document = self.env['documents.document'].search([('name', '=', datas_fname), ('name', '!=', False)])
            if not document:
                document = document.with_context(xml_obj=xml_obj, no_document=True).create({
                    'name': datas_fname,
                    'xunnel_document': True,
                    'type': 'binary',
                    'datas': base64.b64encode(bytes(xml)),
                    'index_content': xml,
                    'mimetype': 'application/xml',
                    'folder_id': folder_id.id,
                    'tag_ids': [(6, 0, tags_type.ids)],
                })
                created.append(document.id)
        self.xunnel_last_sync = max(dates) if dates else self.xunnel_last_sync
        return {
            'created': created,
            'failed': failed,
        }

    def get_xml_sync_action(self):
        result = self._sync_xunnel_documents()
        message_class = 'success'
        message = _(
            "%s xml have been downloaded.") % result.get('created')
        failed = result.get('failed')
        if failed:
            message_class = 'warning'
            message += _(
                "\nAlso %s files have failed at the conversion."
                "\nWe sent you an email with the details of the failed invoices.") % failed
        action_params = {'message': message, 'message_class': message_class}
        return {
            'type': 'ir.actions.client',
            'tag': 'account_xunnel.synchronized_accounts',
            'name': _('Xunnel invoice response.'),
            'target': 'new',
            'params': action_params,
        }

    def get_tag_map(self, key):
        default = self.env['documents.tag']
        values = {
            'I': self.env.ref('invoice_xunnel.ingreso_tag'),
            'E': self.env.ref('invoice_xunnel.egreso_tag'),
            'T': self.env.ref('invoice_xunnel.translado_tag'),
            'P': self.env.ref('invoice_xunnel.reception_tag'),
            'N': self.env.ref('invoice_xunnel.nomina_tag'),
        }
        return values.get(key, default)
