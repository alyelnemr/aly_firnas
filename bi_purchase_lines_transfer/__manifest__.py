# -*- coding: utf-8 -*-
{
    'name': "BI Purchase Lines Transfer",
    'summary': """
        BI Purchase Lines Transfer""",
    'description': """
    """,
    'author': "BI Solutions Development Team",
    'category': 'Purchase',
    'version': '0.1',
    'depends': ['base', 'purchase_stock', 'sale_purchase'],
    'data': [
        'views/purchase_order_inherit.xml',
        'wizard/purchase_lines_transfer.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
