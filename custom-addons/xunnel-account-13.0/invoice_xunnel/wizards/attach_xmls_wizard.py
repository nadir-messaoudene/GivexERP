# pylint: skip-file
# # Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from lxml import objectify
from odoo import _, api, models

TYPE_CFDI22_TO_CFDI33 = {
    'ingreso': 'I',
    'egreso': 'E',
    'traslado': 'T',
    'nomina': 'N',
    'pago': 'P',
}


class AttachXmlsWizard(models.TransientModel):
    _name = 'attach.xmls.wizard'
    _description = "Attach xmls"

    @staticmethod
    def _xml2capitalize(xml):
        """Receive 1 lxml etree object and change all attrib to Capitalize.
        """
        def recursive_lxml(element):
            for attrib, value in element.attrib.items():
                new_attrib = "%s%s" % (attrib[0].upper(), attrib[1:])
                element.attrib.update({new_attrib: value})

            for child in element.getchildren():
                child = recursive_lxml(child)
            return element
        return recursive_lxml(xml)

    @staticmethod
    def _l10n_mx_edi_convert_cfdi32_to_cfdi33(xml):
        """Convert a xml from cfdi32 to cfdi33
        :param xml: The xml 32 in lxml.objectify object
        :return: A xml 33 in lxml.objectify object
        """
        if xml.get('version', None) != '3.2' or xml.get('Version', None) == '3.3':
            return xml
        xml = AttachXmlsWizard._xml2capitalize(xml)
        xml.attrib.update({
            'TipoDeComprobante': TYPE_CFDI22_TO_CFDI33[xml.attrib['TipoDeComprobante']],
            'Version': '3.3',
            # By default creates Payment Complement since that the imported
            # invoices are most imported for this propose if it is not the case
            # then modified manually from odoo.
            'MetodoPago': 'PPD',
        })
        return xml

    def check_xml(self, files, account_id=False):
        response = super(
            AttachXmlsWizard,
            self).check_xml(files=files, account_id=account_id)
        if not self.env.context.get('autofill_enable'):
            return response
        document_obj = self.env['documents.document']
        invoice_obj = self.env['account.move']
        invoice_tag = self.env.ref('invoice_xunnel.with_invoice')
        no_invoice_tag = self.env.ref('invoice_xunnel.without_invoice')
        invoice_files = response.get('invoices')
        for invoice_file in invoice_files:
            invoice_data = invoice_files[invoice_file]
            invoice_id = invoice_data.get('invoice_id', False)
            invoice = invoice_obj.browse(invoice_id)
            document = document_obj.search(
                [('name', '=', invoice_file)], limit=1)
            if not document:
                continue
            document.write({
                'tag_ids': [(3, no_invoice_tag.id, None), (4, invoice_tag.id)],
                'res_id': invoice.id,
                'res_model': 'account.move',
            })
        return response

    @api.model
    def create_partner(self, xml64, key):
        """ It creates the supplier dictionary, getting data from the XML
        Receives an xml decode to read and returns a dictionary with data """
        # Default Mexico because only in Mexico are emitted CFDIs
        try:
            if isinstance(xml64, bytes):
                xml64 = xml64.decode()
            xml_str = base64.b64decode(xml64.replace(
                'data:text/xml;base64,', ''))
            # Fix the CFDIs emitted by the SAT
            xml_str = xml_str.replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            xml = objectify.fromstring(xml_str)
        except BaseException as exce:
            return {
                key: False, 'xml64': xml64, 'where': 'CreatePartner',
                'error': [exce.__class__.__name__, str(exce)]}

        xml = self._l10n_mx_edi_convert_cfdi32_to_cfdi33(xml)
        rfc_emitter = xml.Emisor.get('Rfc', False)
        name = xml.Emisor.get('Nombre', rfc_emitter)

        # check if the partner exist from a previos invoice creation
        partner = self.env['res.partner'].search([
            '&', ('name', '=', name), ('vat', '=', rfc_emitter), '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id)])
        if partner:
            return partner

        partner = self.env['res.partner'].sudo().create({
            'name': name,
            'company_type': 'company',
            'vat': rfc_emitter,
            'country_id': self.env.ref('base.mx').id,
            'company_id': self.env.company.id,
        })
        msg = _('This partner was created when invoice %s%s was added from '
                'a XML file. Please verify that the datas of partner are '
                'correct.') % (xml.get('Serie', ''), xml.get('Folio', ''))
        partner.message_post(subject=_('Info'), body=msg)
        return partner
