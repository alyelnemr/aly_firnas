# -*- coding: utf-8 -*-
{
    'name': "bi_customer_creation_restriction",

    'summary': """
       BI customer creation restriction""",

    'description': """
        This module restricts the customer creation for all users and allow it for only specific group.
    """,

    'author': "BI Solutions Development Team",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base'],

    'data': [
        'data.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False,
    'sequence': 1
}
