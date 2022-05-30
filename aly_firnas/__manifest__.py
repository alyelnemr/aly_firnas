# -*- coding: utf-8 -*-
{
    'name': "Aly - Firnas",
    'summary': "Aly El Nemr, Odoo Development for Firnas Shuman",
    'description': """Aly El Nemr, aly5elnemr@gmail.com, Odoo Development for Firnas Shuman""",
    'author': "Aly El Nemr",
    'depends': ['purchase', 'account'],

    'data': [
        'views/aly_po_report.xml',
        'views/products.xml',
        'views/account_bank_statement.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/purchase_order_line.xml',
        'views/purchase_order_views.xml',
        'views/purchase_order_report.xml',
        'views/purchase_settings.xml',
        'security/groups.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
