# -*- coding: utf-8 -*-
{
    "name": "Givex ESI Report",
    "version": "13.1.0.0.0",
    "category": "Reports",
    "summary": "Givex ESI Report",
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "maintainer": "Syncoria Inc.",
    "depends": ["base", "account"],
    "price": 1000,
    "currency": "USD",
    "license": "AGPL-3",
    "support": "support@syncoria.com",
    "installable": True,
    "application": False,
    "auto_install": False,
    'data': [
        'report/esi_template_header.xml',
        'views/custom_invoice_template.xml',
        'report/custom_invoice_view.xml',
    ],
}
