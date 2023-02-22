{
    "name": "Export TD EFT file generation for Account Batch Payment",
    "version": "13.0.1.0.0",
    "category": "Extra Tool",
    "sequence": 1,
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "summary": """
        Account Batch Payment EFT File for TD.
    """,
    "depends": [
        "base",
        "l10n_mx_edi",
        "l10n_mx_patch_snd",
        "report_xlsx",
        "account_batch_payment",
        "givex_export_barclays_batch_payment",
    ],
    "data": [
        "data/td_batch_payment_data.xml",
        "views/account_view.xml",
        "views/account_batch_payment_views.xml",
        "views/res_bank_views.xml",
    ],
    "license": "AGPL-3",
    "support": "support@syncoria.com",
    "installable": True,
    "application": False,
    "images": [],
}
