# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2020 (https://ingenieuxtech.odoo.com)
# ingenieuxtechnologies@gmail.com
# ingenieuxtechnologies
#
##############################################################################
{
    'name': 'Accounting Report AR/AP Custom',
    'category': 'account',
    'description': """
        Accounting AR/AP report add Account Search and add custom filed in AR Report and export to XLS should have
        custom filed in export.
    """,
    'summary': 'Account AR Report Modifications for V13 Enterprise.',
    'author': 'Ingenieux Technologies',
    'website': 'https://ingenieuxtech.odoo.com/',
    'price': 0.00,
    'currency': 'EUR',
    'images': [
    ],
    'depends': ['base', 'account', 'account_reports'],
    'data': [
        'views/account_move_view.xml',
        'views/external_load_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
