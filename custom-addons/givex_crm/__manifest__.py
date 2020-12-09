# $Id: __manifest__.py,v 1.1 2020/12/08 21:31:34 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex CRM',
    'version': '0.1',
    'summary': 'CRM',
    'author': 'Givex',
    'description': """Customizing CRM leads module""",
    'depends': ['base_setup', 'crm'],
    'data': [
        'views/crm_leads_view.xml',
        'security/crm_leads_data.xml',
    ],
    'demo': [],
    'installable' : True,
    'auto_install': False,
}

