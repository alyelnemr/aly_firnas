# -*- coding: utf-8 -*-
{
    'name': "Global Discount",

    'summary': """
        Universal Discount v13.0""",

    'description': """
        - Apply a field in Sales, Purchase and Invoice module to calculate discount after the order lines are inserted.
        - Discount values can be given in two types:
           
           - In Percent
           - In Amount

        - Can be enabled from (**Note** : Charts of Accounts must be installed).
             
             Settings -> general settings -> invoice 
        
        - Maintains the global tax entries in accounts specified by you (**Note** : To see journal entries in Invoicing:
         (in debug mode) 
             
             Settings -> users -> select user -> Check "Show Full Accounting Features")
        
        - Maintains the global discount entries in accounts specified by you.
        - Label given to you will be used as name given to discount field.
        - Also update the report PDF printout with global discount value.
    """,

    'author': "Ksolves India Pvt. Ltd.",
    'website': "https://www.ksolves.com/",
    'images': ['static/description/Universal-Discount-V13.jpg'],
    'category': 'Sales Management',
    'version': '1.1.1',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'purchase', 'sale_management'],

    'data': [
        'views/ks_sale_order.xml',
        'views/ks_account_invoice.xml',
        'views/ks_purchase_order.xml',
        'views/ks_account_invoice_supplier_form.xml',
        'views/ks_account_account.xml',
        'views/ks_report.xml',
        'views/assets.xml',

    ],

}
