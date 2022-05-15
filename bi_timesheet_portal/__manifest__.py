# -*- coding: utf-8 -*-

{
    'name': 'BI Employee Time sheet Portal',
    'version': '1.0',
    'category': 'Human Resources',
    'license': 'Other proprietary',
    'summary': 'BI Employee Time sheet Portal',
    'description': """
        This module allows your portal employee to view, create and edit his/her own time sheet from portal.
    """,
    'author': 'BI Solutions Development Team',
    'depends': [
        'portal',
        'hr_timesheet',
    ],
    'data': [
        'security/group_security.xml',
        'views/website_portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
