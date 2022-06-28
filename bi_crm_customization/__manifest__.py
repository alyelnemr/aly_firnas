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
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
