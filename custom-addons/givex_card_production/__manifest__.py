# -*- coding: utf-8 -*-                                                                                                                                                                                            
# Part of Odoo. See LICENSE file for full copyright and licensing details.                                                                                                                                         

{
    'name': 'Givex Card Production Orders',
    'version': '0.1',
    'category': 'Sales/Sales',
    'summary': 'Givex Card Production Order changes',
    'description': """This module contains custom field and rule changesfor Sales orders with card production products.""",
    'depends': ['sale', 'product'],
    'data': [
        'views/sale_view.xml',
        'views/sale_portal_templates.xml',
        'report/sale_report_template.xml',
     ],
    'installable': True,
    'auto_install': False
}
