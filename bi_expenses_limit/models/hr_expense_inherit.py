# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from calendar import monthrange
from odoo.tools import float_compare


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    balance = fields.Monetary(string="Balance", currency_field='currency_id', compute="get_balance")
    remaining = fields.Monetary(string="Remaining Amount", currency_field='currency_id', compute="get_remaining")
    show_msg = fields.Boolean(string="Show Message ??", compute="get_show_msg")
    is_employee_advance = fields.Boolean(string="Employee Advance", default=False)

    @api.onchange('is_employee_advance')
    def _onchange_is_employee_advance(self):
        for record in self:
            if record.is_employee_advance:
                product = self.env.ref('bi_expenses_limit.product_petty_cash')
                if product:
                    record.product_id = product.id
                    record.payment_mode = 'company_account'

    def get_balance(self):
        for record in self:
            balance = 0.0
            if record.is_employee_advance:
                date = fields.Datetime.now().date()
                last_of_month = monthrange(date.year, date.month)[1]
                currency = record.currency_id

                move_lines_this_month = self.env['account.move.line'].search([
                    ('date', '>=', date.replace(day=1)),
                    ('date', '<=', date.replace(day=last_of_month)),
                    ('account_id', '=', record.account_id.id),
                    ('parent_state', 'in', ['posted']),
                    # ('expense_id', '!=', record.id)
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
                limit_ids = record.employee_id.limit_ids.filtered(
                    lambda limit: limit.currency_id and limit.currency_id.id == currency.id
                )
                if limit_ids:
                    if len(limit_ids) > 1:
                        raise ValidationError(_("The Employee has many limits for the currency %s." % currency.name))
                    limit = limit_ids[0].limit_amount

                balance = limit - allocated

            record.balance = balance

    def get_remaining(self):
        for record in self:
            remaining = 0
            if record.is_employee_advance:
                remaining = record.balance - record.total_amount
            record.remaining = remaining

    @api.onchange("currency_id", "employee_id")
    def _onchange_set_current_account(self):
        for sheet in self:
            sheet = sheet.sudo()
            if sheet.currency_id and sheet.employee_id:
                currency = sheet.currency_id.id
                account = sheet.employee_id.account_ids.filtered(
                    lambda x:
                    (x.currency_id and (x.currency_id.id == currency)) or
                    (x.company_id and x.company_id.currency_id and (x.company_id.currency_id.id == currency))
                )
                if account:
                    account = account[0]
                sheet.account_id = account.id if account else False

    def get_show_msg(self):
        for sheet in self:
            show_msg = False
            if sheet.is_employee_advance and float_compare(sheet.total_amount, sheet.balance, 5) > 0:
                show_msg = True
            sheet.show_msg = show_msg

    def action_submit_expenses(self):
        res = super(HRExpense, self).action_submit_expenses()
        if 'context' in res:
            res['context']['default_is_employee_advance'] = self.is_employee_advance
            res['context']['employee_advance_date'] = self.date
        return res

    def _get_account_move_line_values(self):
        result = super(HRExpense, self)._get_account_move_line_values()
        sheet_id = self.env.context.get('sheet_id')
        for record in self:
            if record.is_employee_advance and sheet_id:
                for index in result:
                    for element in result[index]:
                        if element['account_id'] not in record.employee_id.account_ids.ids:
                            sheet = self.env['hr.expense.sheet'].browse(sheet_id)
                            if sheet.bank_journal_id:
                                element_type = 'credit' if element['credit'] else 'debit'
                                account_id = False
                                if element_type == 'credit':
                                    if sheet.bank_journal_id.default_credit_account_id:
                                        account_id = sheet.bank_journal_id.default_credit_account_id.id
                                else:
                                    if sheet.bank_journal_id.default_debit_account_id:
                                        account_id = sheet.bank_journal_id.default_debit_account_id.id
                                if account_id:
                                    element['account_id'] = account_id
                        # if element['debit']:
                        #     element['credit'] = element['debit']
                        #     element['debit'] = False
                        # elif element['credit']:
                        #     element['debit'] = element['credit']
                        #     element['credit'] = False
        return result
