# $Id: __manifest__.py,v 1.1 2020/08/20 18:33:29 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Billing Management',
    'version': '0.1',
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
