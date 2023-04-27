{
    "name": "Givex Tax Reports",
    "version": "15.0.1.0.0",
    "category": "Extra Tool",
    "sequence": 1,
    "author": "Syncoria Inc.",
    "website": "https://www.syncoria.com",
    "company": "Syncoria Inc.",
    "summary": """
        Givex Tax reports.
    """,
    "depends": [
        "base",
        "report_csv",
        "report_xlsx",
        "account",
    ],
    "data": [
        "report/account_move_line_report.xml",
        # "views/account_batch_payment_views.xml",
    ],
    "license": "AGPL-3",
    "support": "support@syncoria.com",
    "installable": True,
    "application": False,
    "images": [],
}
