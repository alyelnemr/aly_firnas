# -*- coding: utf-8 -*-
{
    'name': "BI Purchase Approval",
    'summary': "Adding level of approval on RFQ for RFQ Approver",
    'description': """Adding level of approval on RFQ for RFQ Approver""",
    'author': "BI Solutions Development Team",
    'depends': ['purchase'],

    'data': [
        'views/purchase_order_views.xml',
        'security/groups.xml',
        'views/inherit_res_users_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
