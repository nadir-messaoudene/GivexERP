# -*- coding: utf-8 -*-
{
    'name': "l10n_mx_patch_snd",

    'summary': """
        Patching module for production DBs""",

    'description': """
        Workaround for CFDI issue for givex. Do not distribute to others.
    """,

    'author': "SND",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'l10n_mx_edi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'license' : 'OPL-1',
    'installable': True,
    'auto_install': False,
}
