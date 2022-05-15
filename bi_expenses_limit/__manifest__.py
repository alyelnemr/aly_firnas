# -*- coding: utf-8 -*-
{
    'name': "BI Expenses Limit",
    'summary': "BI Expenses Limit",
    'description': """ 
            This module adds new features in expense module.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['base', 'hr_expense', 'account', ],
    'data': [
        'security/expense_limit_security.xml',
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/hr_expenses_sheet_inherit_view.xml',
        'views/hr_expense_inherit_view.xml',
        'views/hr_employee_inherit_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
