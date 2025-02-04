# -*- coding: utf-8 -*-
{
    'name': "Customer Invoice Report",
    'summary': """Print template for Customer Invoices""",
    'description': """Print template for Customer Invoices""",
    'author': "Syncoria Inc.",
    'website': "https://www.syncoria.com",
    'category': 'Report',
    'version': '13.9.0',
    'company': 'syncoria inc.',
    'depends': ['base', 'account'],
    'data': [
        'views/custom_external_layout.xml',
        'views/report_invoice_templates.xml',
        'views/account_report.xml',
        'views/res_config_settings_views.xml',
    ],
    "license": "LGPL-3",
}
