{
    "name": "Barclays Export CSV/Excel File for BACS",
    "version": "15.0.1.0.0",
    "category": "Extra Tool",
    "sequence": 1,
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "summary": """
        Barclays Export CSV/Excel File for BACS.
    """,
    "depends": [
        "base",
        "l10n_us",
        "l10n_mx_edi",
        "l10n_mx_patch_snd",
        "account_batch_payment",
    ],
    "data": [
        "data/account_batch_payment_barclays_data.xml",
        "views/account_batch_payment_views.xml",
        "views/res_bank_views.xml",
    ],
    "license": "AGPL-3",
    "support": "support@syncoria.com",
    "installable": True,
    "application": False,
    "images": [],
}
