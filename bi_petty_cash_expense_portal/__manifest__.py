# -*- coding: utf-8 -*-

{
    'name': 'BI Employee Petty Cash Expense Portal',
    'version': '1.0',
    'category': 'Human Resources',
    'license': 'Other proprietary',
    'summary': 'BI Employee Petty Cash Expense Portal',
    'description': """
        This module allows your portal employee to view, create and edit his/her own petty cash expense requests from portal.
    """,
    'author': 'BI Solutions Development Team',
    'depends': [
        'bi_expenses_limit',
        'bi_expense_portal',
    ],
    'data': [
        'views/website_portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
