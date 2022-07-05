# -*- coding: utf-8 -*-
{
    'name': "BI Analytic Accounts, Analytic Tags",
    'summary': "BI Analytic Accounts, Analytic Tags",
    'description': """ 
            This module:
                - Makes Analytical Accounts & Analytical Tags mandatory field at invoicing, billing, paying expenses, and all screens at accounting module.
                - Adding Analytical Accounts & Analytical Tags to "account.payment' mandatory and move to the payment jouranl in the debit and credit account.
                - Adding Analytical Accounts & Analytical Tags to "stock.picking' mandatory and move to the payment jouranl in the debit and credit account ,
                 note:if the picking come from PO or SO the analytic account and tag will read from the PO or the SO..
     """,
    'author': "BI Solutions Development Team",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base', 'account_accountant', 'hr_expense', 'purchase', 'sale_management'],
    'data': [
        'views/inherit_account_payment_view.xml',
        'views/inherit_picking_view.xml',
        'views/inherit_sales_view.xml',
        'views/inherit_purchase_view.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
