# $Id: __openerp__.py,v 1.19 2015/04/28 21:53:41 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Accounting Reports',
    'version': '0.1',
    'summary': 'Reporting',
    'author': 'Givex',
    'description': """Customizing accounting reports""",
    'depends': ['base_setup', 'product', 'analytic', 'portal', 'digest'],
    ### DEBUG 'data': ['report/account_aged_partner_balance_view.xml'],
    'data': [],
    'demo': [],
    'installable' : True,
    'auto_install': False,
}
