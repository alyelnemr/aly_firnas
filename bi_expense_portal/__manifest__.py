# -*- coding: utf-8 -*-

{
    'name': 'BI Employee Expense Portal',
    'version': '1.0',
    'category': 'Human Resources',
    'license': 'Other proprietary',
    'summary': 'BI Employee Expense Portal',
    'description': """
        This module allows your portal employee to view, create and edit his/her own expense requests from portal.
    """,
    'author': 'BI Solutions Development Team',
    'depends': [
        'portal',
        'hr_expense',
    ],
    'data': [
        'security/expense_security.xml',
        'views/website_portal_templates.xml',
        'views/website_portal_templates2.xml',
    ],
    'installable': True,
    'auto_install': False,
}
