# -*- coding: utf-8 -*-
{
    'name': "BI Opportunity Creation Wizard",
    'summary': """
        BI Opportunity Creation Wizard""",
    'description': """
        Long description of module's purpose
    """,
    'author': "BI Solutions Development Team",
    'category': 'crm',
    'version': '0.1',
    'depends': ['base', 'crm', 'bi_crm_concatenated_name', 'bi_crm_customization'],
    'data': [
        'views/crm_lead_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
