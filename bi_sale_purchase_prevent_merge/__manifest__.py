# -*- coding: utf-8 -*-
{
    'name': "BI Sale Purchase Prevent Merge",
    'summary': """This module prevent checking for existing PO and always create purchase order 
    for purchase order lines coming from sales order line""",
    'description': """  
            This module prevent checking for existing PO and always create purchase order 
            for purchase order lines coming from sales order line
     """,
    'author': "BI Solutions Development Team",
    'category': 'Sales/Sales',
    'version': '0.1',
    'depends': ['base', 'purchase_stock', 'sale_purchase'],
    'data': [
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
