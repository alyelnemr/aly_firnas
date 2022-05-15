# -*- coding: utf-8 -*-
{
    'name': "BI View By Day",
    'summary': "BI view by day",
    'description': """  
            This module adds day to view by in timesheet
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.1',
    'depends': ['base', 'timesheet_grid'],
    'data': [
        'views/inherit_account_analytic.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
