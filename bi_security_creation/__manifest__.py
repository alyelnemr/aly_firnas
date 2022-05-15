# -*- coding: utf-8 -*-
{
    'name': "BI Security Creation",
    'summary': """
        Create security group for creating products, product category, vendors, clients, Analytical Accounts and Analytical tags.""",
    'description': """
    """,
    'author': "BI Solutions Development Team",
    'category': 'Security',
    'version': '0.1',
    'depends': ['base', 'purchase', 'sale_management', 'account_accountant', 'stock'],
    'data': [
        'security/groups.xml',
        'views/inherit_product_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
