# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
            res = "['|', ('company_id', '=', False), ('company_id', '=', [c.id for c in self.env.user.company_ids])]"  # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
                '|', ('company_id', '=', False), ('company_id', 'in', [c.id for c in self.env.user.company_ids]),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id), '|', ('company_id', '=', employee.company_id.id), ('company_id', 'in', [c.id for c in self.env.user.company_ids])]
        return ['|', ('company_id', '=', False), ('company_id', 'in', [c.id for c in self.env.user.company_ids])]

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id,
                                                expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.onchange('project_id')
    def _set_project_data(self):
        for expense in self:
            if expense.project_id:
                expense.company_id = expense.project_id.company_id.id
                expense.analytic_account_id = expense.project_id.analytic_account_id.id

    @api.onchange('analytic_account_id')
    def _set_analytic_account_data(self):
        for expense in self:
            if expense.analytic_account_id:
                analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
                if expense.employee_id:
                    analytic_tag_ids += expense.employee_id.analytic_tag_ids
                expense.analytic_tag_ids = analytic_tag_ids

    @api.model
    def _default_company_id(self):
        return self.project_id.company_id

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_employee_id,
                                  check_company=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True,
                                 tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=False,
                                     domain="[('parent_id', '=', partner_id)]")
    user_to_approve_id = fields.Many2one('res.users', 'User To Approve', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True)
    project_id = fields.Many2one('project.project', 'Project', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_default_company_id)

    # override expense credit account to take journal credit account
    def _get_expense_account_destination(self):
        self.ensure_one()
        result = super(HRExpense, self)._get_expense_account_destination()
        if self.sheet_id.journal_id.default_credit_account_id:
            result = self.sheet_id.journal_id.default_credit_account_id.id
        return result
