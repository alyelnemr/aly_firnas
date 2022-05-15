# -*- coding: utf-8 -*-
{
    'name': "BI Purchase Qty Received",
    'summary': "Allowing to update received Qty when purchase order is locked",
    'description': """Allowing to update received Qty when purchase order is locked""",
    'author': "BI Solutions Development Team",
    'depends': ['purchase'],

    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_inherit_view.xml',
        'wizard/purchase_qty_received_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
