# -*- coding: utf-8 -*-
{
    'name': "BI Salesperson Domain",
    'summary': "BI Salesperson Domain",
    'description': """ 
            This module change salesperson domain in Sales and CRM modules.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'sale_management', 'crm'],
    'data': [
        'views/crm_lead.xml',
        'views/inherit_sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
