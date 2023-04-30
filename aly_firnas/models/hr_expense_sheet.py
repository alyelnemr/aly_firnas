# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    _check_company_auto = False

    @api.model
    def _default_bank_journal_id(self):
        return

    @api.onchange('user_id')
    def _check_user(self):
        for expense in self:
            expense.is_same_user_approver = expense.user_id == self.env.user and expense.state == 'submit'

    expense_line_ids = fields.One2many('hr.expense', 'sheet_id', string='Expense Lines', copy=False, readonly=False, states={
        'post': [('readonly', True)], 'approve': [('readonly', True)], 'done': [('readonly', True)]})
    bank_journal_id = fields.Many2one('account.journal', string='Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=True,
                                      default=_default_bank_journal_id,
                                      domain="[('is_expense_module', '=', True), ('company_id', '=', company_id)]")
    is_same_user_approver = fields.Boolean("Is Same User Approver", compute='_check_user')
    user_id = fields.Many2one('res.users', 'Manager',
                              domain=[('expense_approve', '=', True)],
                              readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True, required=False)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True, string="Paid By")
    account_move_ids = fields.Many2many('account.move', string='All Journal Entries',
                                        copy=False, readonly=True)
    is_account_move_ids = fields.Boolean(compute="_compute_account_move_ids", store=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True,
                                          required=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False,
                                        states={'post': [('readonly', True)], 'done': [('readonly', True)]},
                                        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    state = fields.Selection([
        ('draft', 'To submit'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True, help='Expense Report State')

    @api.depends("account_move_ids")
    def _compute_account_move_ids(self):
        for rec in self:
            rec.is_account_move_ids = len(rec.account_move_ids.ids) > 0

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.address_id = self.employee_id.sudo().address_home_id
        self.department_id = self.employee_id.department_id
        self.user_id = False

    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        move = self.env['account.move'].browse(self.account_move_id.id)
        if move:
            move.write({'state': 'cancel'})
        if self.state in ('done', 'post'):
            self.write({'state': 'approve', 'account_move_id': False})
        else:
            self.write({'state': 'draft', 'account_move_id': False})
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.activity_update()
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def approve_expense_sheets(self):
        if self.user_id.id != self.env.user.id:
            raise UserError(_("You are not allowed to approve these expenses"))
        elif self.user_has_groups('aly_firnas.group_employee_expense_manager_portal'):
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

    @api.onchange('expense_line_ids')
    def _onchange_expense_line_ids(self):
        for rec in self:
            if not rec.analytic_account_id and len(rec.expense_line_ids):
                rec.analytic_account_id = rec.expense_line_ids[0].analytic_account_id
            if not rec.analytic_tag_ids and len(rec.expense_line_ids):
                rec.analytic_tag_ids = rec.expense_line_ids[0].analytic_tag_ids

    @api.model
    def create(self, vals):
        sheet = super(HrExpenseSheet, self.with_context(mail_create_nosubscribe=True, mail_auto_subscribe_no_notify=True)).create(
            vals)
        sheet.activity_update()
        for rec in sheet.expense_line_ids:
            if (rec.product_type in ['product', 'consu']) and (not rec.expense_picking_id or rec.expense_picking_id.state != 'done'):
                raise UserError(_("You cannot create report until you receive products!"))
            if not rec.analytic_account_id and len(rec.expense_line_ids):
                rec.analytic_account_id = rec.expense_line_ids[0].analytic_account_id
            if not rec.analytic_tag_ids and len(rec.expense_line_ids):
                rec.analytic_tag_ids = rec.expense_line_ids[0].analytic_tag_ids
            # rec.create_picking()
        return sheet

    def write(self, vals):
        res = super(HrExpenseSheet, self).write(vals)
        for rec in self:
            if not rec.analytic_account_id and len(rec.expense_line_ids):
                rec.analytic_account_id = rec.expense_line_ids[0].analytic_account_id
            if not rec.analytic_tag_ids and len(rec.expense_line_ids):
                rec.analytic_tag_ids = rec.expense_line_ids[0].analytic_tag_ids
        return res

    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        if any(not sheet.expense_line_ids for sheet in self):
            raise UserError(_("Expenses must have at least one expense item to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount,
                                                  precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date and self.account_move_id.date:
            self.accounting_date = self.account_move_id.date
        else:
            self.accounting_date = fields.Datetime.now()

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    def action_submit_sheet(self):
        for exp in self:
            if not exp.user_id:
                raise UserError(_("You cannot submit report with no manager selected."))
        self.write({'state': 'submit'})
        self.activity_update()
