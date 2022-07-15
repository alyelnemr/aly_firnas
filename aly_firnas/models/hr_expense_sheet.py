# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    user_id = fields.Many2one('res.users', 'Manager', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True, required=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.address_id = self.employee_id.sudo().address_home_id
        self.department_id = self.employee_id.department_id
        self.user_id = False
