# -*- coding: utf-8 -*-
{
    'name': "BI Purchase Re-Invoice Customer",
    'summary': """
        BI Purchase Re-Invoice Customer""",
    'description': """
    """,
    'author': "BI Solutions Development Team",
    'category': 'crm',
    'version': '0.1',
    'depends': ['base', 'purchase', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_inherit.xml',
        'wizard/reinvoice_customer_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
