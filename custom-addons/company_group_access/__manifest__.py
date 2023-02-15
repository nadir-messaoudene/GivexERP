# -*- encoding: utf-8 -*-
##############################################################################
#
# ingenieuxtechnologies@gmail.com
# ingenieuxtechnologies
#
##############################################################################
{
    'name': 'Restrict Multi Company Access',
    'category': 'Technical Settings',
    'description': """
        Allow all Users to switch between Companies, allow only some to check multiple Companies.  This is done by hiding the checkbox unless users are in the "Technical Settings / Can select Multiple Companies" group
    """,
    'summary': 'Hide Multi Company checkbox.',
    'author': 'Ingenieux Technologies',
    'website': 'ingenieuxtechnologies@gmail.com',
    "license": "AGPL-3",
    'price': 49.00,
    'currency': 'USD',
    'images': [
    ],
    'depends': ['base', 'web'],
    'data': [
        'security/res_groups.xml',
        'views/external_load_view.xml',
    ],
    # 'qweb': ['static/src/xml/template_view.xml'],
    "assets": {
        "web.assets_backend": [
            "/company_group_access/static/src/js/company_access.js",
        ],
        'web.assets_qweb': [
            'company_group_access/static/src/xml/*',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
