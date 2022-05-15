# -*- coding: utf-8 -*-

{
    'name': 'Employee Attendance from Web-My Account using Portal User as Employee',
    'version': '1.0',
    'category': 'Website',
    'summary':  """This module allow you to employee(s) who are not real users of system but portal users / external user and it will allow to record check in and checkout as attendance""",
    'description': """
        Odoo Portal Employee Attendance
     """,
    'author' : 'Probuse Consulting Service Pvt. Ltd.',
    'website' : 'www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'depends': [
        'hr_attendance',
        'portal',
        ],
    'data': [
      'security/security.xml',
      'security/ir.model.access.csv',
      'views/website_portal_templates.xml',
     ],
    'installable': True,
    'application': False,
}
