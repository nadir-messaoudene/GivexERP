# $Id: __manifest__.py,v 1.2 2020/11/17 20:08:35 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Billing Management',
    'version': '0.2',
    'summary': 'Invoicing',
    'author': 'Givex',
    'description': """Defining Method to handle XMLPRPC calls for Givex recurring billing.""",
    'depends': ['base_setup', 'account', 'product'],
    ### 'data': ['views/partner_view.xml'],
    'data': [],
    'demo': [],
    'installable' : True,
    'auto_install': False,
}
