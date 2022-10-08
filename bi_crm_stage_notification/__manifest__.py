# -*- coding: utf-8 -*-
{
    'name': "BI CRM Stage Notification",
    'summary': "BI CRM Stage Notification",
    'description': """  
            This module allows users to configure crm stages with groups to send notification when crm stage updated
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.1',
    'depends': ['base', 'crm'],
    'data': [
        'security/security.xml',
        'views/crm_stage.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
