# $Id: __manifest__.py,v 1.3 2021/03/31 13:09:40 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Billing Management',
    'version': '0.3',
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
