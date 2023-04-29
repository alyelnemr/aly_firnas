# -*- coding: utf-8 -*-

import json
import base64
from odoo import http, _, fields
from odoo.http import request
from datetime import datetime, timedelta
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT


class CustomerPortal(CustomerPortal):

    @http.route(['/petty_cash_expense_request_form'], type='http', auth="user", website=True)
    def portal_petty_cash_expense_request_form(self, default_currency=None, default_employee=None, default_company=None, **kw):
        if not request.env.user.has_group(
                'aly_firnas.group_employee_expense_portal') and not request.env.user.has_group(
                'aly_firnas.group_employee_expense_manager_portal'):
            return request.render("aly_firnas.not_allowed_expense_request")
        values = {}

        default_products = request.env['product.product'].sudo().search(
            [('name', '=', 'Employee Petty Cash')])
        products = request.env['product.product'].sudo().search([('can_be_expensed', '=', True)])
        if products:
            products -= default_products

        currencies = request.env['res.currency'].sudo().search([])

        analytic_accounts = request.env['account.analytic.account'].sudo().search([])
        analytic_tags = request.env['account.analytic.tag'].sudo().search([])

        employees = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)])

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers

        if default_currency:
            default_currency = request.env['res.currency'].sudo().browse([int(default_currency)])
        else:
            default_currency = request.env.company.currency_id

        if default_company:
            default_company = request.env['res.company'].sudo().browse([int(default_company)])
        else:
            default_company = request.env.company

        accounts = request.env['account.account'].sudo()
        for emp in employees:
            accounts += emp.account_ids.filtered(lambda x: (x.company_id.id == default_company.id or not x.company_id) and (
                        x.currency_id.id == default_currency.id or not x.currency_id))
        default_account = accounts[0] if accounts else request.env['ir.property'].get(
            'property_account_expense_categ_id',
            'product.category')

        if default_employee:
            default_employee = request.env['hr.employee'].sudo().browse([int(default_employee)])
            currency = default_currency.id
            account = default_employee.account_ids.filtered(
                lambda x:
                (not x.currency_id or (x.currency_id.id == currency)) and
                (not x.company_id or x.company_id.id == default_company.id)
            )
            if account:
                default_account = account[0]

        if accounts:
            accounts -= default_account  # remove the default account

        values.update({
            'products': products,
            'default_products': default_products,
            'currencies': currencies,
            'default_currency': default_currency,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'accounts': accounts,
            'default_account': default_account,
            'analytic_accounts': analytic_accounts,
            'analytic_tags': analytic_tags,
            'today': str(fields.Date.today()),
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_company': request.env.user.company_id,
            'error_fields': '',
        })
        return request.render("bi_petty_cash_expense_portal.petty_cash_expense_request_submit", values)

    @http.route(['/petty_cash_expense_request_submit'], type='http', auth="user", website=True)
    def portal_petty_cash_expense_request_submit(self, **kw):
        vals = request.params.copy()
        if request.params.get('product_id', False):
            product_id = int(request.params.get('product_id'))
            vals.update({
                'product_id': product_id,
            })
        if request.params.get('company_id', False):
            company_id = int(request.params.get('company_id'))
            vals.update({
                'company_id': company_id,
            })

        if request.params.get('analytic_account_id', False):
            analytic_account_id = int(request.params.get('analytic_account_id'))
            vals.update({
                'analytic_account_id': analytic_account_id,
            })

        if request.params.get('analytic_tag_id', False):
            analytic_tag_id = int(request.params.get('analytic_tag_id'))
            vals.update({
                'analytic_tag_ids': [(6, 0, [analytic_tag_id])],
            })
            vals.pop('analytic_tag_id', None)

        if request.params.get('currency_id', False):
            currency_id = int(request.params.get('currency_id'))
            vals.update({
                'currency_id': currency_id,
            })
        if request.params.get('employee_id', False):
            employee_id = int(request.params.get('employee_id'))
            vals.update({
                'employee_id': employee_id,
            })

        vals.pop('attachment', None)

        if request.params.get('manager_id', False):
            vals.pop('manager_id', None)

        date = request.params.get('date')
        vals.update({
            'date': datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) if date else False,
            'is_employee_advance': True,
        })

        created_request = False
        try:
            vals = self._onchange_product_id(vals)

            created_request = request.env['hr.expense'].sudo().create(
                vals)

        except Exception as e:
            if created_request:
                created_request.sudo().unlink()
            values = {}

            default_products = request.env['product.product'].sudo().search(
                [('name', '=', 'Employee Petty Cash')])
            products = request.env['product.product'].sudo().search(
                [('can_be_expensed', '=', True)])
            if products:
                products -= default_products

            currencies = request.env['res.currency'].sudo().search([])
            analytic_accounts = request.env['account.analytic.account'].sudo().search([])
            analytic_tags = request.env['account.analytic.tag'].sudo().search([])

            employees = request.env['hr.employee'].sudo().search(
                [('user_id', '=', request.env.user.id)])

            default_managers = request.env['res.users'].sudo()
            for emp in employees:
                if emp.parent_id and emp.parent_id.user_id:
                    default_managers += emp.parent_id.user_id
            managers = request.env['res.users'].sudo().search([])
            if default_managers:
                managers -= default_managers

            default_currency = request.env.company.currency_id
            default_company = request.env.company

            accounts = request.env['account.account'].sudo()
            for emp in employees:
                accounts += emp.account_ids.filtered(
                    lambda x: (x.company_id.id == default_company.id or not x.company_id) and (
                            x.currency_id.id == default_currency.id or not x.currency_id))
            default_account = accounts[0] if accounts else request.env['ir.property'].get(
                'property_account_expense_categ_id',
                'product.category')

            if accounts:
                accounts -= default_account  # remove the default account

            values.update({
                'products': products,
                'default_products': default_products,
                'currencies': currencies,
                'default_currency': request.env.company.currency_id,
                'employees': employees,
                'managers': managers,
                'default_managers': default_managers,
                'accounts': accounts,
                'default_account': default_account,
                'analytic_accounts': analytic_accounts,
                'analytic_tags': analytic_tags,
                'today': str(fields.Date.today()),
                'companies': request.env.user.company_ids - request.env.user.company_id,
                'default_company': request.env.user.company_id,
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("bi_petty_cash_expense_portal.petty_cash_expense_request_submit", values)

        if created_request:
            if request.params.get('manager_id', False):
                manager_id = int(request.params.get('manager_id'))
            else:
                manager_id = False
            self.action_submit_petty_cash_expenses(created_request, manager_id)
            if request.params.get('attachment', False):
                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment',
                    'type': 'binary',
                    'datas': base64.encodestring(request.params.get('attachment').read()),
                    'store_fname': 'attachment',
                    'res_model': 'hr.expense',
                    'res_id': created_request.id,
                })

            self.submit_expense(created_request)

        return request.render("aly_firnas.thankyou_page")

    def action_submit_petty_cash_expenses(self, expense, manager_id):
        try:
            sheet = request.env['hr.expense.sheet'].sudo().create({
                'employee_id': expense.employee_id.id,
                'name': expense.name,
                'company_id': expense.company_id.id,
                'user_id': manager_id if manager_id else False,
                'is_employee_advance': True,
            })
            expense.sudo().write({
                'sheet_id': sheet.id,
            })
        except:
            pass

    def submit_expense(self, expense):
        if expense:
            try:
                if expense.sheet_id:
                    expense.sheet_id.action_submit_sheet()
                else:
                    self.action_submit_expenses(expense)
                    if expense.sheet_id:
                        expense.sheet_id.action_submit_sheet()
            except:
                pass

    @http.route(['/petty/petty_company_infos'], type='json', auth="public", methods=['POST'], website=True)
    def petty_company_infos(self, company, currency, employee, **kw):
        products = []
        analytic_accounts = []
        analytic_tags = []
        accounts = []
        default_account = []
        if company:
            product_ids = request.env['product.product'].sudo().search(
                ['&', '|', ('name', '=', 'Employee Petty Cash'), ('can_be_expensed', '=', True), '|', ('company_id', '=', int(company)), ('company_id', '=', False)])
            for p in product_ids.filtered(lambda x: x.name == 'Employee Petty Cash'):
                products.append((p.id, p.display_name))
            for p in product_ids.filtered(lambda x: x.name != 'Employee Petty Cash'):
                products.append((p.id, p.display_name))

            # analytic
            analytic_account_ids = request.env['account.analytic.account'].sudo().search(
                ['|', ('company_id', '=', int(company)),  ('company_id', '=', False)])
            for analytic_account in analytic_account_ids:
                analytic_accounts.append((analytic_account.id, analytic_account.display_name))

            analytic_tag_ids = request.env['account.analytic.tag'].sudo().search(
                ['|', ('company_id', '=', int(company)),  ('company_id', '=', False)])
            for analytic_tag in analytic_tag_ids:
                analytic_tags.append((analytic_tag.id, analytic_tag.display_name))

            # Accounts
            if currency:
                default_currency = request.env['res.currency'].sudo().browse([int(currency)])
            else:
                default_currency = request.env.company.currency_id
            account_ids = request.env['account.account'].sudo()
            emp = request.env['hr.employee'].sudo().search([('id', '=', int(employee))]) if employee else False
            if emp:
                currency = default_currency.id
                account_ids += emp.account_ids.filtered(lambda x: (x.company_id.id == int(company) or not x.company_id) and (x.currency_id.id == currency or not x.currency_id ))
                account = emp.account_ids.filtered(
                    lambda x:
                    x.company_id.id == int(company) and (
                    (not x.currency_id or (x.currency_id.id == currency)) )
                )
                if account:
                    default_account = [account[0]]
                    account_ids -= default_account[0]
            if len(default_account):
                accounts.append((default_account[0].id, default_account[0].display_name))
            for a in account_ids:
                accounts.append((a.id, a.display_name))
        return dict(products=products, accounts=accounts, analytic_accounts=analytic_accounts, analytic_tags=analytic_tags)