# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    account_ids = fields.One2many('account.account', 'employee_id', string="Accounts")
    limit_ids = fields.One2many('employee.expense.limit', 'employee_id', string="Limits")
