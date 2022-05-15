# -*- coding: utf-8 -*-

import json
import base64
from odoo.addons.web.controllers.main import Binary
from odoo.tools import image_process
from odoo import http, _, fields
from odoo.http import request
from datetime import datetime, timedelta
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT
from collections import OrderedDict

class CustomerPortal(CustomerPortal):


    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        expenses_obj = request.env['hr.expense']
        if request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            expenses_count = expenses_obj.sudo().search_count([])
        else:
            if employee:
                expenses_count = expenses_obj.sudo().search_count(['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id)])
            else:
                expenses_count = 0
        values.update({
            'expenses_count': expenses_count,
            'employee_data': employee,
            'payment_modes': {
                'own_account': 'Employee (to reimburse)',
                'company_account': 'Company',
            },
            'request_states': {
                'draft': 'To Submit',
                'reported': 'Submitted',
                'approved': 'Approved',
                'done': 'Paid',
                'refused': 'Refused',
            },
        })
        return values

    @http.route(['/my/expenses', '/my/expenses/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expense_requests(self, page=1, sortby=None, filterby=None, **kw):
        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")

        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        expenses_obj = request.env['hr.expense']

        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)

        if request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            domain = []
        else:
            if employee:
                domain = ['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id)]
            else:
                domain = [('employee_id', '=', False)]

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': domain},
        }
        for company in request.env.user.company_ids:
            searchbar_filters.update({
                str(company.id): {'label': company.name, 'domain': domain + [('company_id', '=', company.id)]}
            })
        if not filterby:
            filterby = str(request.env.user.company_id.id)
        domain = searchbar_filters[filterby]['domain']
        # count for pager
        expenses_count = expenses_obj.sudo().search_count(domain)

        # pager
        # pager = request.website.pager(
        pager = portal_pager(
            url="/my/expenses",
            url_args={'sortby': sortby},
            total=expenses_count,
            page=page,
            step=self._items_per_page
        )

        sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'name': {'label': _('Description'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        order = sortings[sortby]['order']

        # content according to pager and archive selected
        expenses = expenses_obj.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'expenses': expenses,
            'page_name': 'expenses',
            'pager': pager,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_sortings': sortings,
            'sortby': sortby,
            'default_url': '/my/expenses',
        })
        return request.render("bi_expense_portal.display_expense_requests", values)

    @http.route(['/my/expenses/<int:expense_id>'], type='http', auth="public", website=True)
    def portal_expense_page(self, expense_id, report_type=None, access_token=None, message=False, download=False, **kw):

        if expense_id:
            expense_sudo = request.env['hr.expense'].sudo().browse([expense_id])
        else:
            return request.redirect('/my/expenses')

        # use sudo to allow accessing/viewing requests for public user
        values = {
            'payment_modes': {
                'own_account': 'Employee (to reimburse)',
                'company_account': 'Company',
            },
            'request_states': {
                'draft': 'To Submit',
                'reported': 'Submitted',
                'approved': 'Approved',
                'done': 'Paid',
                'refused': 'Refused',
            },
        }
        values.update({
            'expense_request': expense_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/my/expenses',
            'bootstrap_formatting': True,
        })

        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values.update({
            'resize_to_48': resize_to_48,
        })

        return request.render('bi_expense_portal.display_expense_request', values)


    @http.route(['/expense_request_form'], type='http', auth="user", website=True)
    def portal_expense_request_form(self, **kw):
        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")
        values = {}
        products = request.env['product.product'].sudo().search([('can_be_expensed', '=', True)])
        currencies = request.env['res.currency'].sudo().search([])
        accounts = request.env['account.account'].sudo().search([('internal_type', '=', 'other')])
        analytic_accounts = request.env['account.analytic.account'].with_user(request.env.ref('base.user_admin').id).search([])
        analytic_tags = request.env['account.analytic.tag'].with_user(request.env.ref('base.user_admin').id).search([])
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers
        values.update({
            'products': products,
            'currencies': currencies,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'accounts': accounts,
            'default_account': request.env['ir.property'].sudo().get('property_account_expense_categ_id', 'product.category'),
            'analytic_accounts': analytic_accounts,
            'analytic_tags': analytic_tags,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_request_submit", values)

    @http.route(['/expense_request_submit'], type='http', auth="user", website=True,methods=['POST'], csrf=False)
    def portal_expense_request_submit(self, **kw):
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

        if request.params.get('manager_id', False):
            vals.pop('manager_id', None)

        if request.params.get('attachment', False):
            vals.pop('attachment', None)

        date = request.params.get('date')
        vals.update({
            'date': datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) if date else False,
        })

        created_request = False
        try:
            vals = self._onchange_product_id(vals)

            created_request = request.env['hr.expense'].sudo().create(vals)

        except Exception as e:
            if created_request:
                created_request.sudo().unlink()
            values = {}
            products = request.env['product.product'].sudo().search([('can_be_expensed', '=', True)])
            currencies = request.env['res.currency'].sudo().search([])
            accounts = request.env['account.account'].sudo().search([('internal_type', '=', 'other')])
            analytic_accounts = request.env['account.analytic.account'].with_user(request.env.ref('base.user_admin').id).search([])
            analytic_tags = request.env['account.analytic.tag'].with_user(request.env.ref('base.user_admin').id).search([])
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])

            default_managers = request.env['res.users'].sudo()
            for emp in employees:
                if emp.parent_id and emp.parent_id.user_id:
                    default_managers += emp.parent_id.user_id
            managers = request.env['res.users'].sudo().search([])
            if default_managers:
                managers -= default_managers

            values.update({
                'products': products,
                'currencies': currencies,
                'default_currency': request.env.company.currency_id,
                'employees': employees,
                'companies': request.env.user.company_ids - request.env.user.company_id,
                'default_company': request.env.user.company_id,
                'managers': managers,
                'default_managers': default_managers,
                'accounts': accounts,
                'default_account': request.env['ir.property'].get('property_account_expense_categ_id',
                                                                  'product.category'),
                'analytic_accounts': analytic_accounts,
                'analytic_tags': analytic_tags,
                'today': str(fields.Date.today()),
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("bi_expense_portal.expense_request_submit", values)

        if created_request:
            if request.params.get('manager_id', False):
                manager_id = int(request.params.get('manager_id'))
            else:
                manager_id = False
            self.action_submit_expenses(created_request, manager_id)
            if request.params.get('attachment', False):
                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment',
                    'type': 'binary',
                    'datas': base64.encodestring(request.params.get('attachment').read()),
                    'store_fname': 'attachment',
                    'res_model': 'hr.expense',
                    'res_id': created_request.id,
                })
            if created_request.sheet_id:
                created_request.sheet_id.action_submit_sheet()

        return request.render("bi_expense_portal.thankyou_page")

    def _onchange_product_id(self, vals):
        product = request.env['product.product'].sudo().browse([int(vals.get('product_id'))]) if vals.get('product_id', False) else False
        if product:
            if not vals.get('name', False):
                vals['name'] = product.display_name or ''
            vals['product_uom_id'] = product.uom_id.id
        return vals

    def action_submit_expenses(self, expense, manager_id=False):
        try:
            sheet = request.env['hr.expense.sheet'].sudo().create({
                'employee_id': expense.employee_id.id,
                'name': expense.name,
                'company_id': expense.company_id.id,
                'user_id': manager_id if manager_id else False,
            })
            expense.sudo().write({
                'sheet_id': sheet.id,
            })
        except:
            pass

    @http.route(['/request_submit'], type='http', auth="user", website=True)
    def portal_submit_expense_request(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense'].sudo().search([('id', '=', int(expense_id))])
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
            if form:
                return request.redirect('/my/expenses/%s'%expense_id)
        return request.redirect('/my/expenses')

    @http.route(['/request_approve'], type='http', auth="user", website=True)
    def portal_approve_expense_request(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense'].sudo().search([('id', '=', int(expense_id))])
            if expense:
                try:
                    if expense.sheet_id:
                        expense.sheet_id.sudo().approve_expense_sheets()
                except:
                    pass
            if form:
                return request.redirect('/my/expenses/%s'%expense_id)
        return request.redirect('/my/expenses')

    @http.route(['/request_refuse'], type='http', auth="user", website=True)
    def portal_refuse_expense_request(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense'].sudo().search([('id', '=', int(expense_id))])
            if expense:
                try:
                    if expense.sheet_id:
                        expense.sheet_id.sudo().refuse_sheet('')
                except:
                    pass
            if form:
                return request.redirect('/my/expenses/%s'%expense_id)
        return request.redirect('/my/expenses/')

    @http.route(['/expense/company_infos'], type='json', auth="public", methods=['POST'], website=True)
    def company_infos(self, company, product, **kw):
        products = []
        analytic_accounts = []
        analytic_tags = []
        accounts = []
        if company:
            product_ids = request.env['product.product'].sudo().search(
                [('can_be_expensed', '=', True), '|', ('company_id', '=', int(company)), ('company_id', '=', False)])
            analytic_account_ids = request.env['account.analytic.account'].with_user(request.env.ref('base.user_admin').id).search(
                ['|', ('company_id', '=', int(company)), ('company_id', '=', False)])
            analytic_tag_ids = request.env['account.analytic.tag'].with_user(
                request.env.ref('base.user_admin').id).search(
                ['|', ('company_id', '=', int(company)), ('company_id', '=', False)])

            for prod in product_ids:
                products.append((prod.id, prod.display_name))
            for analytic_account in analytic_account_ids:
                analytic_accounts.append((analytic_account.id, analytic_account.display_name))
            for analytic_tag in analytic_tag_ids:
                analytic_tags.append((analytic_tag.id, analytic_tag.display_name))

            # Accounts
            account_ids = request.env['account.account'].sudo()
            prod = request.env['product.product'].sudo().search([('id', '=', int(product))]) if product else False
            if prod:
                account_ids += prod.with_context(force_company=int(company)).property_account_expense_id or prod.categ_id.with_context(force_company=int(company)).property_account_expense_categ_id
            for a in account_ids:
                accounts.append((a.id, a.display_name))

        return dict(
            products=products,
            analytic_accounts=analytic_accounts,
            analytic_tags=analytic_tags,
            accounts=accounts,
        )