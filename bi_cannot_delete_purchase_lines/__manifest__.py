# -*- coding: utf-8 -*-
{
    'name': "BI Prevent user from Removing Purchase Lines",
    'summary': "BI Prevent user from Removing Purchase Lines",
    'description': """  
            This module Prevents user from Removing Purchase Lines.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Purchase',
    'version': '0.1',
    'depends': ['base', 'purchase', 'sale'],
    'data': [
        'views/inherit_purchase_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
