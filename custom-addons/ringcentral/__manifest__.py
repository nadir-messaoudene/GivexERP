# See LICENSE file for full copyright and licensing details.
{
    'name': 'RingCentral',
    'version': '13.0.1.0.1',
    'category': 'Customer Relationship Management',
    'description': """
    This is the connector application for RingCentral integration.
    """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['crm', 'sales_team', 'project'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/crm_phonecall_to_phonecall_view.xml',
        'views/crm_phonecall_view.xml',
        'views/res_users_view.xml',
        'views/company_view.xml',
        'wizard/synch_data_wiz.xml',
    ],
    'summary': 'Odoo RingCentral Integration, Telephony Integration',
    'license': 'LGPL-3',
    'qweb': ['static/src/xml/ringcentral.xml', 'static/src/xml/widget.xml'],
    'images': ['static/src/img/ringcentral_logo.png'],
    'installable': True,
    'application': True,
    'price': 599,
    'currency': 'EUR'
}
