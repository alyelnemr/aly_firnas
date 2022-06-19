# -*- coding: utf-8 -*-
{
    'name': "BI Product Bundle Report",
    'summary': "BI Product Bundle Report",
    'description': """ 
            This module adds new fields to sale order lines, and create new print report for sale order.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'sale', 'foss_product_bundle', 'sale_management', 'bi_new_customized_fields',
                'universal_discount', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_form.xml',
        'reports/report.xml',
    ],
    'external_dependencies': {'python': ['textile']},
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
