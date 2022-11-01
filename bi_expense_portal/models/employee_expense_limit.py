# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EmployeeExpenseLimit(models.Model):
    _name = 'employee.expense.limit'
    _description = 'Employee Expense Limit'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    limit_amount = fields.Float(string="Limit", required=1)
    currency_id = fields.Many2one('res.currency', string="Currency", required=1)
