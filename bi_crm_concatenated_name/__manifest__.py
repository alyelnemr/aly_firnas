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
    'depends': ['base', 'crm', 'bi_new_customized_fields'],
    'data': [
        'views/res_config_settings_inherit.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
