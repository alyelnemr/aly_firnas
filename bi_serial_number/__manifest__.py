# -*- coding: utf-8 -*-
{
    'name': "BI Serial Number",
    'summary': "BI Serial Number",
    'description': """ 
            This module adds new checkbox to product form, and depending on it's value, some fields will be required in lot.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['base', 'stock', 'product_expiry'],
    'data': [
        'views/product_product_form.xml',
        'views/stock_move_line_form.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
