# -*- coding: utf-8 -*-
{
    'name': "Customer Invoice Report",
    'summary': """Print template for Customer Invoices""",
    'description': """Print template for Customer Invoices""",
    'author': "Syncoria Inc.",
    'website': "https://www.syncoria.com",
    'category': 'Report',
    'version': '0.1.3',
    'depends': ['base', 'account'],
    'data': [
        'views/custom_external_layout.xml',
        'views/report_invoice.xml',
        'views/report_invoice_templates.xml',
        'views/account_report.xml',
    ],
    "license": "LGPL-3",
}
