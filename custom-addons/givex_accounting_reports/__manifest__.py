# $Id: __manifest__.py,v 1.2 2020/09/24 17:29:56 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Accounting Reports',
    'version': '0.2',
    'summary': 'Reporting',
    'author': 'Givex & Ingenieux Technologies',
    'description': """Customizing accounting reports""",
    'depends': ['base_setup', 'account', 'account_reports'],
    'data': [
        'views/account_move_view.xml',
        'views/external_load_view.xml',
    ],
    'demo': [],
    "license": "AGPL-3",
    "assets": {
        "web.assets_backend": [
            "givex_accounting_reports/static/src/js/account_reports.js",
        ],
    },
    'installable': True,
    'auto_install': False,
}
