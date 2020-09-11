# $Id: __manifest__.py,v 1.1 2020/08/31 15:17:26 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Accounting Reports',
    'version': '0.1',
    'summary': 'Reporting',
    'author': 'Givex',
    'description': """Customizing accounting reports""",
    'depends': ['base_setup', 'product', 'analytic', 'portal', 'digest', 'account_reports'],
    'data': [],
    'demo': [],
    'installable' : True,
    'auto_install': False,
}
