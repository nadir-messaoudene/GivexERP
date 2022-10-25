# $Id: __manifest__.py,v 1.1 2020/12/08 21:31:34 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.
{
    'name': 'Givex Worksheet Report',
    'version': '0.1',
    'summary': 'Givex Worksheet Report for Kalex company',
    'description': """Givex make new report Worksheet Report for Kalex company""",
    'category': 'Operations/Field Service',
    'author': 'Givex',
    'depends': ['industry_fsm'],
    'data': [
        'views/field_service_report.xml',
        'views/worksheet_report_projecttask.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
