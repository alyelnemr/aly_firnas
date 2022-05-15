# -*- coding: utf-8 -*-
{
    'name': "BI Send Notification to Specific Group",
    'summary': "BI send mail notification with updated state to specific group",
    'description': """  
            This module sends mail notification with updated state to specific groups
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.1',
    'depends': ['base', 'crm'],
    'data': [
        'views/inherit_res_config_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
