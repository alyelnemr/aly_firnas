# -*- coding: utf-8 -*-
{
    'name': "BI CRM Concatenated Name",
    'summary': """
        BI CRM Concatenated Name""",
    'description': """
    """,
    'author': "BI Solutions Development Team",
    'category': 'crm',
    'version': '0.1',
    'depends': ['base', 'crm', 'bi_new_customized_fields', 'bi_crm_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_inherit.xml',
        'views/crm_lead_views.xml',
        'views/res_config_settings_inherit.xml',
        'views/crm_type_views.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
