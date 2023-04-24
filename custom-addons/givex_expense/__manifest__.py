{
    "name": "Givex HR Expense",
    "summary": "Givex HR Expense",
    "author": "Syncoria Inc",
    "website": "https://www.syncoria.com",
    "category": "Human Resources/Expenses",
    "version": "1.0",
    "depends": ["base", "hr_expense"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/hr_expense_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "OPL-1",
}
