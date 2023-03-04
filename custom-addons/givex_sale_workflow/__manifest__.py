# -*- coding: utf-8 -*-                                                                                                                                                                                            
# Part of Odoo. See LICENSE file for full copyright and licensing details.                                                                                                                                         

{
    'name': 'Givex Sale Workflow',
    'version': '0.7',
    'category': 'Sales/Sales',
    'summary': 'Givex Sale Workflow',
    'description': """This module contains custom workflow for Sales orders.""",
    "license": "AGPL-3",
    'depends': ['sales_team', 'payment', 'portal', 'utm', 'sale', 'product'],
    'data': [
        'views/product_views.xml',
        'security/sale_security.xml',
        'views/sale_view.xml',
     ],
    'installable': True,
    'auto_install': False
}
