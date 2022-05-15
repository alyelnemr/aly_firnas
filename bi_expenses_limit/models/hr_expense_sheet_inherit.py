# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from calendar import monthrange
from odoo.tools import float_compare


class HRExpensesSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    need_approval = fields.Boolean(string="Need Approval?", compute="get_need_approval")
    can_approve = fields.Boolean(string="Can Approve?", compute="get_can_approve")
    employee_advance_currency_id = fields.Many2one('res.currency', string="Advance Currency",
                                                   compute="get_advance_currency", store=True)
    balance = fields.Monetary(string="Balance", currency_field='employee_advance_currency_id', compute="get_balance")
    remaining = fields.Monetary(string="Remaining Amount", currency_field='employee_advance_currency_id',
                                compute="get_remaining")
    show_msg = fields.Boolean(string="Show Message?", compute="get_show_msg")
    expense_manager_id = fields.Many2one(
        'res.users', string='Expense Responsible',
        related="employee_id.expense_manager_id",
        help="User responsible of expense approval. Should be Expense Manager."
    )
    general_manager_id = fields.Many2one('res.users', string='General Manager')
    is_employee_advance = fields.Boolean(string="Employee Advance")

    @api.onchange('user_id')
    def set_general_manager_id(self):
        for record in self:
            if not record.user_id:
                continue
            employee = self.env['hr.employee'].search([('user_id', '=', record.user_id.id)], limit=1)
            if employee:
                manager = employee.parent_id

                record.general_manager_id = manager.user_id.id if manager else False

    @api.model
    def deactivate_rules(self):
        rule_1 = self.env.ref('hr_expense.ir_rule_hr_expense_sheet_approver')
        rule_2 = self.env.ref('hr_expense.ir_rule_hr_expense_sheet_employee')
        rule_3 = self.env.ref('hr_expense.ir_rule_hr_expense_approver')

        if rule_1:
            rule_1.write({'active': False})
        if rule_2:
            rule_2.write({'active': False})
        if rule_3:
            rule_3.write({
                'domain_force': """
                [
                    '|', '|', '|', '|',
                    ('employee_id.user_id', '=', user.id),
                    ('employee_id.department_id.manager_id.user_id', '=', user.id),
                    ('employee_id.parent_id.user_id', '=', user.id),
                    ('employee_id.expense_manager_id', '=', user.id),
                    ('sheet_id.user_id', '=', user.id)
                ]
                """
            })
        return

    @api.depends('is_employee_advance', 'expense_line_ids', 'currency_id')
    def get_advance_currency(self):
        for record in self:
            if record.is_employee_advance and record.expense_line_ids:
                record.employee_advance_currency_id = record.expense_line_ids[0].currency_id.id
            else:
                record.employee_advance_currency_id = record.currency_id.id

    def approve_expense_sheets(self):
        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    def get_balance(self):
        for record in self:
            balance = 0
            if record.is_employee_advance:
                account = False
                date = fields.Datetime.now().date()
                last_of_month = monthrange(date.year, date.month)[1]
                currency = record.employee_advance_currency_id
                expense_lines = self.env['hr.expense'].sudo().search([('sheet_id', '=', record.id)])
                if len(expense_lines) == 1:
                    account = expense_lines[0].account_id
                if account:
                    move_lines_this_month = self.env['account.move.line'].search([
                        ('date', '>=', date.replace(day=1)),
                        ('date', '<=', date.replace(day=last_of_month)),
                        ('account_id', '=', account.id),
                        ('parent_state', 'in', ['posted']),
                        # ('expense_id', 'not in', record.expense_line_ids.ids)
                    ])
                    from_currency = self.env.company.currency_id
                    to_currency = currency

                    allocated = 0
                    for move_line in move_lines_this_month:
                        if from_currency != to_currency:
                            allocated += from_currency._convert((move_line.debit - move_line.credit), to_currency, record.company_id,
                                               move_line.date)
                        else:
                            allocated += (move_line.debit - move_line.credit)

                    limit = 0.0
                    limit_ids = record.employee_id.sudo().limit_ids.filtered(
                        lambda limit: limit.currency_id and limit.currency_id.id == currency.id
                    )
                    if limit_ids:
                        if len(limit_ids) > 1:
                            raise ValidationError(
                                _("The Employee has many limits for the currency %s." % currency.name))
                        limit = limit_ids[0].limit_amount
                    balance = limit - allocated
            record.balance = balance

    def get_remaining(self):
        for record in self:
            remaining = 0
            if record.is_employee_advance:
                if record.currency_id != record.employee_advance_currency_id:
                    remaining = record.balance - record.currency_id._convert(record.total_amount,
                                                                             record.employee_advance_currency_id,
                                                                             record.company_id, fields.Date.today())
                else:
                    remaining = record.balance - record.total_amount
            record.remaining = remaining

    @api.depends("total_amount", "employee_id", "currency_id", "is_employee_advance")
    def get_need_approval(self):
        for sheet in self:
            if sheet.is_employee_advance:
                if sheet.currency_id != sheet.employee_advance_currency_id:
                    sheet.need_approval = (float_compare(sheet.balance, sheet.currency_id._convert(
                        sheet.total_amount, sheet.employee_advance_currency_id, sheet.company_id, fields.Date.today()),
                                                         5) < 0)
                else:
                    sheet.need_approval = (float_compare(sheet.balance, sheet.total_amount, 5) < 0)
            else:
                sheet.need_approval = False

    def get_can_approve(self):
        for sheet in self:
            if self._context.get('portal_uid', False):
                portal_user = self.env['res.users'].browse([self._context.get('portal_uid')])
                if sheet.need_approval is True:
                    sheet.can_approve = portal_user.has_group('bi_expenses_limit.group_hr_user_approve_all_sheet')
                else:
                    sheet.can_approve = portal_user.id == sheet.user_id.id or \
                                        portal_user.has_group('bi_expenses_limit.group_hr_user_approve_inbounds_sheet') or \
                                        portal_user.has_group('bi_expenses_limit.group_hr_user_approve_all_sheet')
            else:
                if sheet.need_approval is True:
                    sheet.can_approve = self.user_has_groups('bi_expenses_limit.group_hr_user_approve_all_sheet')
                else:
                    sheet.can_approve = self.env.uid == sheet.user_id.id or \
                                        self.user_has_groups('bi_expenses_limit.group_hr_user_approve_inbounds_sheet') or \
                                        self.user_has_groups('bi_expenses_limit.group_hr_user_approve_all_sheet')

    def get_show_msg(self):
        for sheet in self:
            show_msg = False
            if sheet.is_employee_advance:
                if sheet.currency_id != sheet.employee_advance_currency_id:
                    total_amount = sheet.currency_id._convert(sheet.total_amount, sheet.employee_advance_currency_id, sheet.company_id, fields.Date.today())
                else:
                    total_amount = sheet.total_amount
                if float_compare(total_amount, sheet.balance, 5) > 0:
                    show_msg = True

            sheet.show_msg = show_msg