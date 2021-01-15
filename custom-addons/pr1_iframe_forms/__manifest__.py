# -*- coding: utf-8 -*-
{
    'name': 'Forms integration with 3rd party websites',
    'author': 'PR1',
    'live_test_url':'https://statictest.pr1.xyz/contactus.html',
    'version': '1',
    'summary': 'Integrates Odoo forms with any 3rd party website.',
    'description': 'This module will integrate odoo forms with any 3rd party website, this includes websites such as wix, Joomla! Wordpress, DotNetNuke, static html, custom sites etc.',
    'category': 'Website',
    "website": "https://pr1.xyz/",
    'license': 'OPL-1',
    "price": 120.00,
    'application':True,
    'sequence': 1,
    'installable': True,
    'auto_install': False,
    "depends" : ["base","website"],
    'images': [
        'static/description/banner.jpg'
    ],
    "data" : [
            'security/security.xml',
              'menus/menus.xml','views/general_config.xml',
              'security/ir.model.access.csv',      
              'data/default_data.xml'
              ],
    "test" : [
    ],
}
