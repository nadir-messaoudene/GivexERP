# -*- coding: utf-8 -*-
{
    'name': "Odoo Sync Payment Website",

    'summary': """
        Add feature for website in payment""",

    'description': """
        Add feature for website in payment
    """,

    'author': "Syncoria Inc.",
    'website': "http://www.syncoria.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payments',
    'version': '15.1.1',

    # any module necessary for this one to work correctly
    'depends': ['os_payment', 'website_sale'],

    # always loaded
    'data': [
        # Moneris Checkout Website Part
        'payment_apps/payment_moneris_checkout/views/payment_moneris_templates.xml',
        # Bambora Checkout Website Part
        'payment_apps/odoo_bambora_checkout/views/payment_bambora_checkout_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    "price": 1000,
    "currency": "USD",
    "license": "OPL-1",
    "support": "support@syncoria.com",
}
