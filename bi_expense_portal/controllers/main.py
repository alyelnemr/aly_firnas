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
        # if not filterby:
        #     filterby = str(request.env.user.company_id.id)
        # domain = searchbar_filters[filterby]['domain']
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
        currencies = request.env['res.currency'].sudo().search([])
        projects = request.env['project.project'].sudo().search([])
        vendors = request.env['res.partner'].sudo().search([])
        vendor_id = vendors[0].id
        company = projects[0].company_id.id
        products = request.env['product.product'].sudo().search(
            [('can_be_expensed', '=', True), '|', ('company_id', '=', int(company)), ('company_id', '=', False)])
        tax_ids = request.env['account.tax'].sudo().search([('company_id', '=', projects[0].company_id.id)])
        vendor_contact_id = request.env['res.partner'].sudo().search([('parent_id', '=', vendor_id)])
        accounts = request.env['account.account'].sudo().search([('internal_type', '=', 'other')])
        analytic_accounts = request.env['account.analytic.account'].sudo().browse([projects[0].analytic_account_id.id])
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        analytic_tags = employees[0].analytic_tag_ids + analytic_accounts[0].analytic_tag_ids

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers
        values.update({
            'products': products,
            'vendors': vendors,
            'projects': projects,
            'vendor_contact_id': vendor_contact_id,
            'currencies': currencies,
            'tax_ids': tax_ids,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'accounts': accounts,
            'default_account': request.env['ir.property'].sudo().get('property_account_expense_categ_id', 'product.category'),
            'analytic_account_id': analytic_accounts,
            'analytic_tag_id': analytic_tags,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_request_submit", values)

    @http.route(['/expense_request_form/<int:expense_id>'], type='http', auth="user", website=True)
    def portal_expense_request_edit(self, expense_id, **kw):
        if expense_id:
            expense_sudo = request.env['hr.expense'].sudo().browse([expense_id])
        else:
            return request.redirect('/my/expenses')

        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")
        values = {}
        currencies = request.env['res.currency'].sudo().search([])
        projects = request.env['project.project'].sudo().search([])
        vendors = request.env['res.partner'].sudo().search([])
        vendor_id = vendors[0].id
        company = projects[0].company_id.id
        products = request.env['product.product'].sudo().search(
            [('can_be_expensed', '=', True), '|', ('company_id', '=', int(company)), ('company_id', '=', False)])
        tax_ids = request.env['account.tax'].sudo().search([('company_id', '=', projects[0].company_id.id)])
        vendor_contact_id = request.env['res.partner'].sudo().search([('parent_id', '=', vendor_id)])
        accounts = request.env['account.account'].sudo().search([('internal_type', '=', 'other')])
        analytic_accounts = request.env['account.analytic.account'].sudo().browse([projects[0].analytic_account_id.id])
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        analytic_tags = employees[0].analytic_tag_ids + analytic_accounts[0].analytic_tag_ids

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers
        values.update({
            'expense_sudo': expense_sudo,
            'products': products,
            'vendors': vendors,
            'projects': projects,
            'vendor_contact_id': vendor_contact_id,
            'currencies': currencies,
            'tax_ids': tax_ids,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'accounts': accounts,
            'default_account': request.env['ir.property'].sudo().get('property_account_expense_categ_id', 'product.category'),
            'analytic_account_id': analytic_accounts,
            'analytic_tag_id': analytic_tags,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_request_edit", values)

    @http.route(['/expense_request_delete/<int:expense_id>'], type='http', auth="user", website=True)
    def portal_expense_request_delete(self, expense_id, **kw):
        if expense_id:
            expense_sudo = request.env['hr.expense'].sudo().browse([expense_id])
            expense_sudo.sudo().unlink()
        else:
            return request.redirect('/my/expenses')
        return request.render("bi_expense_portal.delete_page")

    @http.route(['/expense_request_submit'], type='http', auth="user", website=True,methods=['POST'], csrf=False)
    def portal_expense_request_submit(self, **kw):
        vals = request.params.copy()
        if request.params.get('partner_id', False):
            partner_id = int(request.params.get('partner_id'))
            vals.update({
                'partner_id': partner_id,
            })
        if request.params.get('vendor_contact_id', False):
            vendor_contact_id = int(request.params.get('vendor_contact_id'))
            vals.update({
                'vendor_contact_id': vendor_contact_id,
            })
        if request.params.get('product_id', False):
            product_id = int(request.params.get('product_id'))
            vals.update({
                'product_id': product_id,
            })
        if request.params.get('project_id', False):
            project_id = int(request.params.get('project_id'))
            vals.update({
                'project_id': project_id,
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

        list_all = request.httprequest.form.getlist('analytic_tag_id')

        if list_all:
            vals.update({
                'analytic_tag_ids': [(6, 0, list_all)],
            })
        elif request.params.get('analytic_tag_id', False):
            analytic_tag_id = int()
            vals.update({
                'analytic_tag_ids': [(6, 0, [analytic_tag_id])],
            })
        vals.pop('analytic_tag_id', None)

        if request.params.get('tax_ids', False):
            tax_ids = int(request.params.get('tax_ids'))
            vals.update({
                'tax_ids': [(6, 0, [tax_ids])],
            })

        if 'manager_id' in vals.keys():
            vals.pop('manager_id', None)

        if 'attachment' in vals.keys():
            vals.pop('attachment', None)

        date = request.params.get('date')
        vals.update({
            'date': datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) if date else False,
        })
        hdn_expense_id = False
        if 'hdn_expense_id' in vals.keys():
            hdn_expense_id = int(vals.get('hdn_expense_id'))
            vals.pop('hdn_expense_id', None)
        if 'hdn_vendor_contact_id' in vals.keys():
            vals.pop('hdn_vendor_contact_id', None)

        created_request = False
        try:
            vals = self._onchange_product_id(vals)

            if hdn_expense_id:
                expense = request.env['hr.expense'].sudo().search([('id', '=', int(hdn_expense_id))])
                expense.write(vals)
            else:
                created_request = request.env['hr.expense'].sudo().create(vals)

        except Exception as e:
            if created_request:
                created_request.sudo().unlink()
            values = {}
            currencies = request.env['res.currency'].sudo().search([])
            vendors = request.env['res.partner'].sudo().search([])
            projects = request.env['project.project'].sudo().search([])
            vendor_id = vendors[0].id
            company = projects[0].company_id.id
            products = request.env['product.product'].sudo().search(
                [('can_be_expensed', '=', True), '|', ('company_id', '=', int(company)), ('company_id', '=', False)])
            vendor_contact_id = request.env['res.partner'].sudo().search([('parent_id', '=', vendor_id)])
            tax_ids = request.env['account.tax'].sudo().search([('company_id', '=', company)])
            accounts = request.env['account.account'].sudo().search([('internal_type', '=', 'other')])
            analytic_accounts = request.env['account.analytic.account'].sudo().search([('id', '=', projects[0].analytic_account_id.id)])
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
            analytic_tags = employees[0].analytic_tag_ids + analytic_accounts[0].analytic_tag_ids

            default_managers = request.env['res.users'].sudo()
            for emp in employees:
                if emp.parent_id and emp.parent_id.user_id:
                    default_managers += emp.parent_id.user_id
            managers = request.env['res.users'].sudo().search([])
            if default_managers:
                managers -= default_managers

            values.update({
                'products': products,
                'vendors': vendors,
                'vendor_contact_id': vendor_contact_id,
                'projects': projects,
                'currencies': currencies,
                'tax_ids': tax_ids,
                'default_currency': request.env.company.currency_id,
                'employees': employees,
                'companies': request.env.user.company_ids - request.env.user.company_id,
                'default_company': request.env.user.company_id,
                'managers': managers,
                'default_managers': default_managers,
                'accounts': accounts,
                'default_account': request.env['ir.property'].get('property_account_expense_categ_id',
                                                                  'product.category'),
                'analytic_account_id': analytic_accounts,
                'analytic_tag_id': analytic_tags,
                'today': str(fields.Date.today()),
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("bi_expense_portal.expense_request_submit", values)

        # this code for creating expense report, ignore this step by a request from Eng. Mostafa El Bedawy
        # if created_request:
        #     if request.params.get('manager_id', False):
        #         manager_id = int(request.params.get('manager_id'))
        #     else:
        #         manager_id = False
        #     self.action_submit_expenses(created_request, manager_id)
        #     if request.params.get('attachment', False):
        #         request.env['ir.attachment'].sudo().create({
        #             'name': 'attachment',
        #             'type': 'binary',
        #             'datas': base64.encodestring(request.params.get('attachment').read()),
        #             'store_fname': 'attachment',
        #             'res_model': 'hr.expense',
        #             'res_id': created_request.id,
        #         })
        #     if created_request.sheet_id:
        #         created_request.sheet_id.action_submit_sheet()

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
            analytic_account_ids = request.env['account.analytic.account'].with_user(
                request.env.ref('base.user_admin').id).search(
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
                account_ids += prod.with_context(
                    force_company=int(company)).property_account_expense_id or prod.categ_id.with_context(
                    force_company=int(company)).property_account_expense_categ_id
            for a in account_ids:
                accounts.append((a.id, a.display_name))

        return dict(
            products=products,
            analytic_accounts=analytic_accounts,
            analytic_tags=analytic_tags,
            accounts=accounts,
        )

    @http.route(['/expense/vendor_contacts'], type='json', auth="public", website=True)
    def vendor_contacts(self, vendor, **kw):
        vendor_contacts = []
        if vendor:
            vendor_id = int(vendor)
            res_partner_contacts = request.env['res.partner'].sudo().search(
                [('parent_id', '=', vendor_id)])
            for item in res_partner_contacts:
                vendor_contacts.append((item.id, item.name))
        return dict(
            vendor_contacts=vendor_contacts,
        )

    @http.route(['/expense/project_change'], type='json', auth="public", website=True)
    def project_change(self, project_id_str, **kw):
        analytic_account_data = []
        company_id = []
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        analytic_tags_data = []
        for item_tag in employees[0].analytic_tag_ids:
            analytic_tags_data.append((item_tag.id, item_tag.name))
        if project_id_str:
            project_id = int(project_id_str)
            res_project_data = request.env['project.project'].sudo().search(
                [('id', '=', project_id)])
            for item in res_project_data:
                company_id = item.company_id.id
            for item in res_project_data:
                analytic_account_data.append((item.analytic_account_id.id, item.analytic_account_id.name))
                for item_tag in item.analytic_account_id.analytic_tag_ids:
                    analytic_tags_data.append((item_tag.id, item_tag.name))
        return dict(
            company_data=company_id,
            analytic_account_data=analytic_account_data,
            analytic_tags_data=analytic_tags_data,
        )

    @http.route(['/expense/product_change'], type='json', auth="public", website=True)
    def product_change(self, product_id_str, **kw):
        product_data = []
        if product_id_str:
            product_id = int(product_id_str)
            res_product_data = request.env['product.product'].sudo().search(
                [('id', '=', product_id)])
            for item in res_product_data.product_tmpl_id._get_product_accounts()['expense']:
                product_data.append((item.id, item.name))
        return dict(
            default_account=product_data,
        )

    @http.route(['/expense/compute_all'], type='json', auth="public", website=True)
    def compute_all(self, unit_amount_str, quantity_str, tax_id_str, **kw):
        vendor_contacts = []
        total_amount = 0
        if unit_amount_str and quantity_str and tax_id_str:
            unit_amount = float(unit_amount_str)
            quantity = float(quantity_str)
            tax_id = int(tax_id_str)
            tax_obj = request.env['account.tax'].sudo().search([('id', '=', tax_id)])
            total_amount = round( (unit_amount * quantity) + (unit_amount * quantity * (tax_obj.amount / 100)), 2)
        return dict(
            total_amount=total_amount,
        )
