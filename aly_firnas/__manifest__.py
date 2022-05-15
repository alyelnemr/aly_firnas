# -*- coding: utf-8 -*-
{
    'name': "Aly - Firnas",
    'summary': "Aly El Nemr, Odoo Development for Firnas Shuman",
    'description': """Aly El Nemr, aly5elnemr@gmail.com, Odoo Development for Firnas Shuman""",
    'author': "Aly El Nemr",
    'depends': ['purchase'],

    'data': [
        'views/purchase_order_views.xml',
        'security/groups.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
