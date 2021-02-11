# -*- coding: utf-8 -*-
{
    'name': 'Easy Application of Outstanding credits for Customers',
    'version': '13.0',
    'category': 'Accounting',
    'license': 'OPL-1',
    'summary' : 'Easy Application of Outstanding credits for Customers',
    'description': """

====================================
Easy Application of Outstanding credits for Customers
    """,
    'author' : 'Backendevs',
    'website': 'http://www.backendevs.com',
    'maintaner' : 'Backendevs',    
    'depends': ['account'],
    'currency' : 'USD',
    'price' : 30,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/easy_reconciliation_view.xml'
    ],
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}