# -*- coding: utf-8 -*-
{
    'name': "Zendesk Connector",
    'summary': """
        Zendesk Support puts all your customer support interactions in one place.""",
    'description': """
        Odoo Zendesk Support puts all your customer support interactions in one place, 
        so communication is seamless, personal, and efficient–which means more 
        productive agents and satisfied customers.
    """,
    'author': "Techloyce",
    'website': "http://www.techloyce.com",
    'category': 'Customer Relationship Management',
    'version': '15.1.0',
    'price': 299,
    'currency': 'EUR',
    'license': 'OPL-1',
    'depends': ['base', 'mail', 'contacts', 'helpdesk', 'sale_management', 'account'],
    'images': [
            'static/description/banner.gif',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/configuration.xml',
        'views/helpdesk_tickets.xml',
        'views/zendesk.xml',
        'views/res_partner.xml',
        'data/schedulers.xml',
    ],
    'installable': True,
    'application': True,
}
