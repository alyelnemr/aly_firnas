# -*- coding: utf-8 -*-
{
    'name': "BI Actual Submission Date",
    'summary': "BI actual submission date with notification",
    'description': """  
            This module sends mail notification with updated state to specific groups
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.1',
    'depends': ['base', 'bi_new_customized_fields'],
    'data': [
        'security/security.xml',
        'views/inherit_res_config_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
