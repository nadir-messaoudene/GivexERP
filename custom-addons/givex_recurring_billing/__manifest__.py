# $Id: __manifest__.py,v 1.6 2021/09/13 13:48:23 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Billing Management',
    'version': '0.5',
    'summary': 'Invoicing',
    'author': 'Givex',
    "license": "AGPL-3",
    'description': """Defining Method to handle XMLPRPC calls for Givex recurring billing.""",
    'depends': ['base_setup', 'account', 'product'],
    ### 'data': ['views/partner_view.xml'],
    'data': [
            'security/ir.model.access.csv',
        ],
    'demo': [],
    'installable' : True,
    'auto_install': False,
}
