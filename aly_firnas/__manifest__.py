# -*- coding: utf-8 -*-
{
    'name': "Aly - Firnas",
    'summary': "Aly El Nemr, Odoo Development for Firnas Shuman",
    'description': """Aly El Nemr, aly5elnemr@gmail.com, Odoo Development for Firnas Shuman""",
    'author': "Aly El Nemr",
    'depends': ['base', 'purchase', 'web_domain_field',
                'sale', 'sale_expense', 'account_asset', 'sale_management', 'account', 'bi_product_bundle_report'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/wh_email.xml',
        'views/aly_po_report.xml',
        'views/aly_rfq_report.xml',
        'views/res_users.xml',
        'views/product.xml',
        'views/projects.xml',
        'views/hr_expense.xml',
        'views/hr_expense_sheet.xml',
        'views/hr_expense_settings.xml',
        'views/hr_employee.xml',
        'views/account_analytic_account.xml',
        'views/account_bank_statement.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/sale_template_views.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/stock_move_line.xml',
        'views/stock_production_lot.xml',
        'views/purchase_order_line.xml',
        'views/purchase_order.xml',
        'views/purchase_order_report.xml',
        'views/purchase_settings.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
