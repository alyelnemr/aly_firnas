# -*- coding: utf-8 -*-
{
    'name': "Aly - Firnas",
    'summary': "Aly El Nemr, Odoo Development for Firnas Shuman",
    'description': """Aly El Nemr, aly5elnemr@gmail.com, Odoo Development for Firnas Shuman""",
    'author': "Aly El Nemr",
    'depends': ['purchase', 'sale', 'sale_management', 'account', 'bi_product_bundle_report'],

    'data': [
        'security/ir.model.access.csv',
        'views/aly_po_report.xml',
        'views/aly_rfq_report.xml',
        'views/product.xml',
        # 'views/hr_expense.xml',
        'views/account_bank_statement.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/sale_template_views.xml',
        'views/sale_order.xml',
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
