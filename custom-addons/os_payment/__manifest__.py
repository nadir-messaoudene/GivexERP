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

        # 2. Payment: Bambora Checkout
        # 'os_payment/payment_apps/odoo_bambora_checkout/security/ir.model.access.csv',
        'payment_apps/odoo_bambora_checkout/views/payment_bambora_templates.xml',
        'payment_apps/odoo_bambora_checkout/views/sale_order.xml',
        'payment_apps/odoo_bambora_checkout/views/payment_views.xml',
        'payment_apps/odoo_bambora_checkout/views/response_status.xml',
        'payment_apps/odoo_bambora_checkout/data/account_payment_methods.xml',


        # ======================================================================================
        # =============================POS Payment Methods======================================
        # ======================================================================================
        # 1. Clover Cloud Invoice Part
        'payment_apps/odoo_clover_cloud/security/ir.model.access.csv',
        'payment_apps/odoo_clover_cloud/views/clover_device.xml',
        'payment_apps/odoo_clover_cloud/views/account_journal.xml',
        'payment_apps/odoo_clover_cloud/views/account_move.xml',
        'payment_apps/odoo_clover_cloud/views/account_payment_register.xml',
        'payment_apps/odoo_clover_cloud/views/account_payment.xml',


        # 2. Clover Cloud Invoice Part
        'payment_apps/payment_moneris_cloud/views/account_move.xml',
        'payment_apps/payment_moneris_cloud/views/account_journal.xml',
        'payment_apps/payment_moneris_cloud/views/account_payment.xml',
        'payment_apps/payment_moneris_cloud/views/account_payment_register.xml',
        'payment_apps/payment_moneris_cloud/wizard/sh_message_wizard.xml',
        


    ],
    'assets':
        {
            'web.assets_frontend':
                [
                    'os_payment/payment_apps/payment_moneris_checkout/static/src/css/style.css',
                    'os_payment/payment_apps/payment_moneris_checkout/static/src/js/payment_form_inherit.js',
                    "os_payment/payment_apps/odoo_bambora_checkout/static/src/js/payment_form.js",
                    "os_payment/payment_apps/odoo_bambora_checkout/static/src/css/style.css",
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
