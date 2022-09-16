# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    _check_company_auto = False

    @api.onchange('user_id')
    def _check_user(self):
        for expense in self:
            expense.is_same_user_approver = expense.user_id == self.env.user and expense.state == 'submit'

    is_same_user_approver = fields.Boolean("Is Same User Approver", compute='_check_user')
    user_id = fields.Many2one('res.users', 'Manager',
                              domain=[('expense_approve', '=', True)],
                              readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True, required=True)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True, string="Paid By")
    account_move_ids = fields.Many2many('account.move', string='All Journal Entries',
                                        copy=False, readonly=True)

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
        if self.state in ('done', 'post'):
            self.write({'state': 'approve', 'account_move_id': False})
        else:
            self.write({'state': 'draft', 'account_move_id': False})
        self.activity_update()
        return True

    def approve_expense_sheets(self):
        if self.user_id.id != self.env.user.id:
            raise UserError(_("You are not allowed to approve these expenses"))
        if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers and not self.user_has_groups(
                    'hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
                raise UserError(_("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    def action_view_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        # operator = 'child_of' if self..is_company else '='
        action['domain'] = [('id', 'in', self.account_move_ids.ids)]
        action['view_mode'] = 'tree'
        action['context'] = {}
        return action
