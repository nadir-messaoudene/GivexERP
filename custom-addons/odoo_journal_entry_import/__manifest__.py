# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Journal Entry Import from Excel',
    'version': '1.3',
    'price': 15.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """This module allow you to import journal items from excel file.""",
    'description': """
    Odoo Journal Entry Import
    This module import journal items from excel file
Journal Entry Import from Excel
Import Journal Items
Import Items
Import journal
journal entry import
import journal
import journal entry odoo
import journal items
journal items import
journal import
opening entry import
opening balance import
partner balance import
journal entry excel import
journal items excel import
    """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/bank.png'],
    # 'live_test_url' : 'https://youtu.be/kTWippsomeg',
    'live_test_url':'https://youtu.be/fjDu5yJ9xPw',
    'category': 'Accounting',
    'depends': [
                'account',
                ],
    'data':[
        'wizard/import_excel_wizard.xml',
        'views/journal_view.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
