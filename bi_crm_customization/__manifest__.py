# -*- coding: utf-8 -*-
{
    'name': "BI CRM Customization",
    'summary': "BI crm customization",
    'description': """  
            This module make changes at crm.lead
     """,
    'author': "BI Solutions Development Team",
    'category': 'CRM',
    'version': '0.5',
    'depends': ['base', 'crm', 'sale', 'sale_management', 'sale_crm', 'bi_crm_stage_notification'],
    'data': [
        'data/service_cron.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/crm_type.xml',
        'views/crm_lead.xml',
        'views/crm_lead_kanban.xml',
        'views/crm_lead_stage.xml',
        'views/crm_lead_convert_opportunity_views.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
