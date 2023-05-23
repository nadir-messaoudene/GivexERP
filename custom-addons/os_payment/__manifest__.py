# -*- coding: utf-8 -*-
{
    'name': "Odoo Sync Payment Apps",
    'version': '15.1.2',
    'summary': """Odoo Sync Payment Apps""",
    'description': """Odoo Sync Payment Apps""",
    'category': 'Payments',
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "maintainer": "Syncoria Inc.",
    'depends': ['odoosync_base', 'account_payment'],
    'data': [
        'views/omni_account_payment.xml',
        # ======================================================================================
        # =============================Payment:Payment Gateway==================================
        # ======================================================================================
        # 1. Payment: Moneris Checkout
        'payment_apps/payment_moneris_checkout/security/ir.model.access.csv',
        'payment_apps/payment_moneris_checkout/data/account.xml',
        'payment_apps/payment_moneris_checkout/data/payment_acquirer_data.xml',
        'payment_apps/payment_moneris_checkout/views/payment_moneris_templates.xml',
        'payment_apps/payment_moneris_checkout/views/payment_views.xml',

    ],
    'assets':
        {
            'web.assets_frontend':
                [
                    'os_payment/payment_apps/payment_moneris_checkout/static/src/css/style.css',
                    'os_payment/payment_apps/payment_moneris_checkout/static/src/js/payment_form_inherit.js',
                ],
    },


    "price": 1000,
    "currency": "USD",
    "license": "OPL-1",
    "support": "support@syncoria.com",
    "installable": True,
    "application": False,
    "auto_install": False,
    "pre_init_hook": "pre_init_check",
}
