# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    user_id = fields.Many2one('res.users', 'Manager', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True, required=True)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True, string="Paid By")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.address_id = self.employee_id.sudo().address_home_id
        self.department_id = self.employee_id.department_id
        self.user_id = False

    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        move = self.env['account.move'].browse(self.account_move_id.id)
        if move:
            move.write({'state': 'cancel'})
        self.write({'state': 'draft', 'account_move_id': False})
        self.activity_update()
        return True
