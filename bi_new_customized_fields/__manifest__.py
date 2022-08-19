# -*- coding: utf-8 -*-
{
    'name': "BI New Customized Fields",
    'summary': "BI new customized fields",
    'description': """ 
            This module adds new fields to Payroll, Sales, and Project modules.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['base', 'sale', 'sale_management', 'hr_payroll', 'crm', 'project', 'account_accountant', 'hr',
                'sale_crm', 'bi_status_of_project'],
    'data': [
        'views/inherit_account_bank_statement_model_view.xml',
        'views/inherit_res_partner_model_view.xml',
        'views/sales_settings.xml',
        'views/inherit_hr_employee_model.xml',
        'views/inherit_project_project_model_view.xml',
        'views/inherit_sale_order_model_view.xml',
        'views/inherit_account_payment_model_view.xml',
        'views/inherit_project_task_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
