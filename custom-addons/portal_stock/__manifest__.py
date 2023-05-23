# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Portal Stock',
    'version': '15.0.1.0.0',
    'category': 'Warehouse',
    'author': "Syncoria Inc",
    'company': "Syncoria Inc",
    'maintainer': 'Syncoria Inc',
    'website': "https://www.syncoria.com",
    'summary': """Portal Product On hnad Qty""",
    'description': """
This module adds access rules to your portal if stock and portal are installed.
==========================================================================================
    """,
    'depends': ['sale_stock', 'portal'],
    'data': [
        # 'security/portal_security.xml',
        # 'security/ir.model.access.csv',
        'views/portal_inherited.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    "application": False,
}
