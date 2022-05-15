# -*- coding: utf-8 -*-
{
    'name': "BI Products Modification",

    'summary': """Bi Products Modification""",

    'description': "This module:"
                   "- prevent users from adding new products in SO, PO, picking and Invoice."
                   "- change ordered_qty widget to integer",

    'author': "Bi Development Team",
    'website': "http://bisolutions.com/",
    'category': 'Sales',
    'version': '12.0.0.1.0',
    'depends': ['sale_management', 'sale', 'purchase', 'stock', 'account'],

    'data': [
        'views/sale_order_inherit_view.xml',
        'views/purchase_order_inherit_view.xml',
        'views/account_invoice_inherit_view.xml',
        'views/stock_picking_inherit_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
