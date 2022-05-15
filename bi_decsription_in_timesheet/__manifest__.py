# -*- coding: utf-8 -*-
{
    'name': "BI Description in Time sheet",
    'summary': "BI description in time sheet",
    'description': """  
            This module adds description field to timesheet
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
