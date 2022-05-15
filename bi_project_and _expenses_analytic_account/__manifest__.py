# -*- coding: utf-8 -*-
{
    'name': "BI Project/Expenses Analytic Accounts",
    'summary': """
        This module prevents users to create analytic accounts in project and expenses form.""",
    'description': """
    """,
    'author': "BI Solutions Development Team",
    'category': 'Project',
    'version': '0.1',
    'depends': ['base', 'project', 'hr_expense'],
    'data': [
        'views/inherit_project_view.xml',
        'views/inherit_expenses_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
