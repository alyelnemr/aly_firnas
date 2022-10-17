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
        expenses_reports_obj = request.env['hr.expense.sheet']
        if request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            expenses_count = expenses_obj.sudo().search_count([])
            expenses_reports_count = expenses_obj.sudo().search_count([])
        else:
            if employee:
                expenses_count = expenses_obj.sudo().search_count(['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id)])
                expenses_reports_count = expenses_reports_obj.sudo().search_count(['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id)])
            else:
                expenses_count = 0
                expenses_reports_count = 0
        values.update({
            'expenses_count': expenses_count,
            'expenses_reports_count': expenses_reports_count,
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
            'report_states': {
                'draft': 'Draft',
                'submit': 'Submitted',
                'post': 'Posted',
                'approve': 'Approved',
                'done': 'Paid',
                'cancel': 'Refused',
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

    @http.route(['/my/expenses_reports', '/my/expenses_reports/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expense_reports(self, page=1, sortby=None, filterby=None, **kw):
        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")

        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        expenses_reports_obj = request.env['hr.expense.sheet']

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
        expenses_count = expenses_reports_obj.sudo().search_count(domain)

        # pager
        # pager = request.website.pager(
        pager = portal_pager(
            url="/my/expenses_reports",
            url_args={'sortby': sortby},
            total=expenses_count,
            page=page,
            step=self._items_per_page
        )

        sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Description'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        order = sortings[sortby]['order']

        # content according to pager and archive selected
        expenses = expenses_reports_obj.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'expenses_reports': expenses,
            'page_name': 'expenses_reports',
            'pager': pager,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_sortings': sortings,
            'sortby': sortby,
            'default_url': '/my/expenses_reports',
        })
        return request.render("bi_expense_portal.display_expense_reports", values)

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

    @http.route(['/my/expenses_reports/<int:expense_report_id>'], type='http', auth="public", website=True)
    def portal_expense_report_page(self, expense_report_id, report_type=None, access_token=None, message=False, download=False, **kw):

        if expense_report_id:
            expense_sudo = request.env['hr.expense.sheet'].sudo().browse([expense_report_id])
            if not expense_sudo.payment_mode:
                expense_sudo.payment_mode = 'company_account'
        else:
            return request.redirect('/my/expenses_reports')

        # use sudo to allow accessing/viewing requests for public user
        values = {
            'payment_modes': {
                'own_account': 'Employee (to reimburse)',
                'company_account': 'Company',
            },
            'report_states': {
                'draft': 'Draft',
                'submit': 'Submitted',
                'post': 'Posted',
                'approve': 'Approved',
                'done': 'Paid',
                'cancel': 'Refused',
            },
        }
        values.update({
            'expense_report': expense_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/my/expenses_reports',
            'bootstrap_formatting': True,
        })

        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values.update({
            'resize_to_48': resize_to_48,
        })

        return request.render('bi_expense_portal.display_expense_report', values)

    @http.route(['/expense_request_form'], type='http', auth="user", website=True)
    def portal_expense_request_form(self, **kw):
        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")
        picking_type_obj = request.env['stock.picking.type']
        values = {}
        currencies = request.env['res.currency'].sudo().search([])
        projects = request.env['project.project'].sudo().search([])
        dest_address_id = request.env['res.partner'].sudo().search([])
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

        picking_type_id = picking_type_obj.sudo().search(
            [('code', '=', 'incoming'), ('company_id', '=', request.env.user.company_id.id)]
        )

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
            'dest_address_id': dest_address_id,
            'projects': projects,
            'vendor_contact_id': vendor_contact_id,
            'currencies': currencies,
            'tax_ids': tax_ids,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'picking_type_id': picking_type_id,
            'default_managers': default_managers,
            'accounts': accounts,
            'default_account': request.env['ir.property'].sudo().get('property_account_expense_categ_id', 'product.category'),
            'analytic_account_id': analytic_accounts,
            'analytic_tag_id': analytic_tags,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_request_submit", values)

    @http.route(['/expense_report_form'], type='http', auth="user", website=True)
    def portal_expense_report_form(self, **kw):
        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")
        values = {}
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        expenses_obj = request.env['hr.expense']
        expenses_to_be_added = expenses_obj.sudo().search(
            ['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id),
             ('state', '=', 'draft'),
             ('company_id', '=', request.env.user.company_id.id),
             ('sheet_id', '=', False)])

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers
        values.update({
            'expenses_to_be_added': expenses_to_be_added,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_report_submit", values)

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

    @http.route(['/expense_report_form/<int:expense_report_id>'], type='http', auth="user", website=True)
    def portal_expense_report_edit(self, expense_report_id, **kw):
        if expense_report_id:
            expense_sudo = request.env['hr.expense.sheet'].sudo().browse([expense_report_id])
        else:
            return request.redirect('/my/expenses_reports')

        if not request.env.user.has_group('bi_expense_portal.group_employee_expense_portal') and not request.env.user.has_group('bi_expense_portal.group_employee_expense_manager_portal'):
            return request.render("bi_expense_portal.not_allowed_expense_request")
        values = {}
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        expenses_obj = request.env['hr.expense']
        expenses_to_be_added = expenses_obj.sudo().search(
            ['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id),
             ('state', '=', 'draft'),
             ('company_id', '=', request.env.user.company_id.id),
            ('sheet_id', '=', False)])

        default_managers = request.env['res.users'].sudo()
        for emp in employees:
            if emp.parent_id and emp.parent_id.user_id:
                default_managers += emp.parent_id.user_id
        managers = request.env['res.users'].sudo().search([])
        if default_managers:
            managers -= default_managers
        values.update({
            'expense_sudo': expense_sudo,
            'expenses_to_be_added': expenses_to_be_added - expense_sudo.expense_line_ids,
            'companies': request.env.user.company_ids - request.env.user.company_id,
            'default_currency': request.env.company.currency_id,
            'default_company': request.env.user.company_id,
            'employees': employees,
            'managers': managers,
            'default_managers': default_managers,
            'today': str(fields.Date.today()),
            'error_fields': '',
        })
        return request.render("bi_expense_portal.expense_report_edit", values)

    @http.route(['/expense_request_delete/<int:expense_id>'], type='http', auth="user", website=True)
    def portal_expense_request_delete(self, expense_id, **kw):
        if expense_id:
            expense_sudo = request.env['hr.expense'].sudo().browse([expense_id])
            expense_sudo.sudo().unlink()
        else:
            return request.redirect('/my/expenses')
        return request.render("bi_expense_portal.delete_page")

    @http.route(['/expense_report_delete/<int:expense_report_id>'], type='http', auth="user", website=True)
    def portal_expense_report_delete(self, expense_report_id, **kw):
        if expense_report_id:
            expense_sudo = request.env['hr.expense.sheet'].sudo().browse([expense_report_id])
            expense_sudo.sudo().unlink()
        else:
            return request.redirect('/my/expenses_reports')
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

        if request.params.get('currency_id', False):
            currency_id = int(request.params.get('currency_id'))
            vals.update({
                'currency_id': currency_id,
            })
        if request.params.get('picking_type_id', False):
            picking_type_id = int(request.params.get('picking_type_id'))
            vals.update({
                'picking_type_id': picking_type_id,
            })

        if request.params.get('project_id', False):
            project_id = int(request.params.get('project_id'))
            vals.update({
                'project_id': project_id,
            })
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        vals.update({
            'employee_id': employee_id.id,
        })
        projects = request.env['project.project'].sudo().browse(project_id)
        if projects:
            company_id = projects.company_id
            vals.update({
                'company_id': company_id.id,
            })
            analytic_account_id = projects.analytic_account_id
            res_product_data = request.env['product.product'].sudo().search(
                [('id', '=', product_id)])
            product_accounts = res_product_data.product_tmpl_id.with_context(force_company=company_id.id)._get_product_accounts()[
                'expense']
            for account_id in product_accounts:
                vals.update({
                    'account_id': account_id.id,
                })

        if analytic_account_id:
            analytic_tags = employee_id[0].analytic_tag_ids + analytic_account_id.analytic_tag_ids
            vals.update({
                'analytic_account_id': analytic_account_id.id,
            })
            vals.update({
                'analytic_tag_ids': [(6, 0, analytic_tags.ids)],
            })

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

        return request.render("bi_expense_portal.thankyou_page") if not hdn_expense_id else request.render("bi_expense_portal.edit_page")

    @http.route(['/expense_report_submit'], type='http', auth="user", website=True,methods=['POST'], csrf=False)
    def portal_expense_report_submit(self, **kw):
        vals = request.params.copy()
        if request.params.get('company_id', False):
            company_id = int(request.params.get('company_id'))
            vals.update({
                'company_id': company_id,
            })

        list_all = request.httprequest.form.getlist('to_be_added_ids')
        if list_all:
            list_all = list(map(int, list_all))
            vals.update({
                'expense_line_ids': [(6, 0, list_all)],
            })
        else:
            vals.update({
                'expense_line_ids': [(5, 0, {})],
            })
        vals.pop('to_be_added_ids', None)

        if request.params.get('employee_id', False):
            employee_id = int(request.params.get('employee_id'))
            vals.update({
                'employee_id': employee_id,
            })
        if 'user_id' in vals.keys():
            manager_id = int(request.params.get('user_id'))
            vals.update({
                'user_id': manager_id,
            })

        hdn_expense_id = False
        if 'hdn_expense_id' in vals.keys():
            hdn_expense_id = int(vals.get('hdn_expense_id'))
            vals.pop('hdn_expense_id', None)

        created_request = False
        try:
            vals = self._onchange_product_id(vals)

            if hdn_expense_id:
                expense = request.env['hr.expense.sheet'].sudo().search([('id', '=', int(hdn_expense_id))])
                expense.write(vals)
            else:
                created_request = request.env['hr.expense.sheet'].sudo().create(vals)

        except Exception as e:
            if created_request:
                created_request.sudo().unlink()
            values = {}
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])

            default_managers = request.env['res.users'].sudo()
            for emp in employees:
                if emp.parent_id and emp.parent_id.user_id:
                    default_managers += emp.parent_id.user_id
            managers = request.env['res.users'].sudo().search([])
            if default_managers:
                managers -= default_managers
            values.update({
                'description': vals['description'],
                'companies': request.env.user.company_ids - request.env.user.company_id,
                'default_currency': request.env.company.currency_id,
                'default_company': request.env.user.company_id,
                'employees': employees,
                'managers': managers,
                'default_managers': default_managers,
                'today': str(fields.Date.today()),
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("bi_expense_portal.expense_report_submit", values)

        return request.render("bi_expense_portal.thankyou_report_page") if not hdn_expense_id else request.render("bi_expense_portal.edit_report_page")

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

    @http.route(['/report_submit'], type='http', auth="user", website=True)
    def portal_submit_expense_report(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense.sheet'].sudo().search([('id', '=', int(expense_id))])
            if expense:
                try:
                    expense.action_submit_sheet()
                except Exception as e:
                    pass
            if form:
                return request.redirect('/my/expenses_reports/%s'%expense_id)
        return request.redirect('/my/expenses_reports')

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

    @http.route(['/report_approve'], type='http', auth="user", website=True)
    def portal_approve_expense_report(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense.sheet'].sudo().search([('id', '=', int(expense_id))])
            if expense:
                try:
                    expense.sudo().approve_expense_sheets()
                except:
                    pass
            if form:
                return request.redirect('/my/expenses_reports/%s'%expense_id)
        return request.redirect('/my/expenses_reports')

    @http.route(['/report_refuse'], type='http', auth="user", website=True)
    def portal_refuse_expense_report(self, **kw):
        expense_id = request.params.get('id')
        form = request.params.get('form', False)
        if expense_id:
            expense = request.env['hr.expense.sheet'].sudo().search([('id', '=', int(expense_id))])
            if expense:
                try:
                    expense.sudo().refuse_sheet('')
                except:
                    pass
            if form:
                return request.redirect('/my/expenses_reports/%s'%expense_id)
        return request.redirect('/my/expenses_reports/')

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
    def project_change(self, project_id_str, product_id_str=None, **kw):
        analytic_account_data = []
        company_id = False
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        analytic_tags_data = []
        for item_tag in employees[0].analytic_tag_ids:
            analytic_tags_data.append((item_tag.id, item_tag.name))
        if project_id_str and product_id_str:
            product_data = []
            project_id = int(project_id_str)
            product_id = int(product_id_str)
            res_project_data = request.env['project.project'].sudo().search([('id', '=', project_id)], limit=1)
            for item in res_project_data:
                company_id = item.company_id.id
            for item in res_project_data:
                analytic_account_data.append((item.analytic_account_id.id, item.analytic_account_id.name))
                for item_tag in item.analytic_account_id.analytic_tag_ids:
                    analytic_tags_data.append((item_tag.id, item_tag.name))
            res_product_data = request.env['product.product'].sudo().search(
                [('id', '=', product_id)])
            product_accounts = res_product_data.product_tmpl_id.with_context(force_company=company_id)._get_product_accounts()[
                'expense']
            for item in product_accounts:
                product_data.append((item.id, item.name))
                show_picking_type_id = res_product_data.type in ('product', 'consu')
        return dict(
            company_data=company_id,
            analytic_account_data=analytic_account_data,
            analytic_tags_data=analytic_tags_data,
            default_account=product_data,
            show_picking_type_id=show_picking_type_id,
        )

    @http.route(['/expense/product_change'], type='json', auth="public", website=True)
    def product_change(self, product_id_str, company_id_str=None, **kw):
        product_data = []
        if product_id_str and company_id_str:
            company_id = request.env['res.company'].sudo().browse(int(company_id_str))
            product_id = int(product_id_str)
            res_product_data = request.env['product.product'].sudo().search(
                [('id', '=', product_id)])
            product_accounts = res_product_data.product_tmpl_id.with_context(force_company=company_id.id)._get_product_accounts()['expense']
            for item in product_accounts:
                product_data.append((item.id, item.name))
                show_picking_type_id = res_product_data.type in ('product', 'consu')
        return dict(
            default_account=product_data,
            show_picking_type_id=show_picking_type_id,
        )

    @http.route(['/expense/compute_all'], type='json', auth="public", website=True)
    def compute_all(self, unit_amount_str=None, quantity_str=None, discount_str=None, tax_id_str=None, **kw):
        sub_total = 0
        total_amount = 0
        if unit_amount_str and quantity_str and tax_id_str and discount_str:
            unit_amount = float(unit_amount_str)
            discount = float(discount_str)
            unit_amount = unit_amount - (unit_amount * discount / 100)
            quantity = float(quantity_str)
            sub_total = (unit_amount * quantity)
            tax_id = int(tax_id_str)
            tax_obj = request.env['account.tax'].sudo().search([('id', '=', tax_id)])
            total_amount = round( sub_total + (unit_amount * quantity * (tax_obj.amount / 100)), 2)
        return dict(
            sub_total=sub_total,
            total_amount=total_amount,
        )

    @http.route(['/expense/currency_change'], type='json', auth="public", website=True)
    def compute_currency_change(self, currency_id_str=None, company_id_str=None, discount_str=None, tax_id_str=None, **kw):
        if company_id_str and currency_id_str:
            company_id = request.env['res.company'].sudo().browse(int(company_id_str))
            currency_id = request.env['res.currency'].sudo().browse(int(currency_id_str))
        return dict(
            is_readonly=company_id.currency_id == currency_id,
        )

    @http.route(['/expense/picking_type_change'], type='json', auth="public", website=True)
    def picking_type_change(self, picking_type_id_str=None, **kw):
        show_location = False
        if picking_type_id_str:
            picking_type_id = request.env['stock.picking.type'].sudo().browse(int(picking_type_id_str))
            show_location = picking_type_id.default_location_dest_id.usage == 'customer'
        return dict(
            show_location_dest_id=show_location,
        )
