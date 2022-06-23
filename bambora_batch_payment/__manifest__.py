{
    "name": "Bambora Batch Payment",
    "version": "13.0.1.0.0",
    "category": "Accounts",
    "summary": "Bambora Bank-to-Bank EFT/ACH/Batch Payment",
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "maintainer": "Syncoria Inc.",
    "depends": ["account", "payment", "sale"],
    "images": [
        "static/description/banner.png",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_bamboraeft.xml",
        "views/batch_payment_tracking_views.xml",
        "views/inherited_account_move_views.xml",
        "views/partner_view.xml",
        "views/sale_order.xml",
        "data/journal.xml",
        "data/bamboraeft.xml",
        "data/cron_data.xml",
        "data/account_payment_method.xml",
        "data/custom_email.xml",
    ],
    "price": 1000,
    "currency": "USD",
    "license": "AGPL-3",
    "support": "support@syncoria.com",
    "installable": True,
    'application': False,
    'auto_install': False,
    "pre_init_hook": "pre_init_check",
    "post_init_hook": "create_missing_journal_for_acquirers",
    "uninstall_hook": "uninstall_hook",
}
