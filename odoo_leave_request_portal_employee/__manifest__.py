# -*- coding: utf-8 -*-

{
    'name': 'Employee Leaves from Web-My Account using Portal User as Employee',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Employee Leaves from Web-My Account using Portal User as Employee',
    'description': """ 
    This module allow your portal employee to view, create and edit own leaves from my account
""",
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'https://www.probuse.com',
    'images': ['static/description/img1.jpg'],
    'depends': [
        'portal',
        'hr_holidays',
        'resource',
        'mail',
        'calendar',
    ],
    'data': [
        'security/holiday_security.xml',
        'security/ir.model.access.csv',
        'views/expense_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
