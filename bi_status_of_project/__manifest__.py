# -*- coding: utf-8 -*-
{
    'name': "BI Project Status",
    'summary': "BI Project Status",
    'description': """ 
            This module adds new status to project.project
     """,
    'author': "BI Solutions Development Team",
    'category': 'Project',
    'version': '0.1',
    'depends': ['base', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_project_project_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
