# -*- coding: utf-8 -*-
{
    'name': "BI CRM Customization",
    'summary': "BI crm customization",
    'description': """  
            This module make changes at crm.lead
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.1',
    'depends': ['base', 'crm', 'bi_crm_stage_notification'],
    'data': [
        'data/service_cron.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/crm_stage.xml',
        'views/crm_type.xml',
        'views/crm_lead.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
