# -*- coding: utf-8 -*-
{
    'name': "Invoice Report",

    'summary': """
        Print template for purchase order 
        """,

    'description': """
        Print template for purchase order 
    """,

    'author': "Syncoria Inc.",
    'website': "https://www.syncoria.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1.3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'views/custom_external_layout.xml',
        'views/report_invoice_templates.xml',
        'report/invoice_print_reports.xml',
        'views/account_report.xml',
    ],
    "license": "LGPL-3",
}
