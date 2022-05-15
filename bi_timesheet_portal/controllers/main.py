# -*- coding: utf-8 -*-

import json
import base64
from odoo.addons.web.controllers.main import Binary
from odoo.tools import image_process
from odoo import http, _, fields
from odoo.http import request
from datetime import datetime
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from collections import OrderedDict
import math

class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1)
        projects = request.env['project.project'].sudo().search(
            []).filtered(
            lambda p: request.env.user.partner_id.id in p.message_follower_ids.mapped('partner_id').ids)

        timesheets_obj = request.env['account.analytic.line']
        # if request.env.user.has_group('bi_timesheet_portal.group_employee_timesheet_manager_portal'):
        #     timesheets_count = timesheets_obj.with_user(request.env.ref('base.user_admin').id).search_count([])
        # else:
        if employee:
            timesheets_count = timesheets_obj.sudo().search_count(
                ['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id),('project_id','in',projects.ids)])
        else:
            timesheets_count = 0
        values.update({
            'timesheets_count': timesheets_count,
            'employee_data': employee,
        })
        return values

    @http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_timesheet_requests(self, page=1, date=None, sortby=None, filterby=None, search=None,
                                     search_in='project', groupby='none', **kw):
        if not request.env.user.has_group(
                'bi_timesheet_portal.group_employee_timesheet_portal') and not request.env.user.has_group(
            'bi_timesheet_portal.group_employee_timesheet_manager_portal'):
            return request.render("bi_timesheet_portal.not_allowed_timesheet_request")

        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        timesheets_obj = request.env['account.analytic.line']

        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1)

        sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'name': {'label': _('Description'), 'order': 'name'},
            'project_id': {'label': _('Project'), 'order': 'project_id'},
            'task_id': {'label': _('Task'), 'order': 'task_id'},
            'employee_id': {'label': _('Employee'), 'order': 'employee_id'},
        }

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        # extends filterby criteria with project the customer has access to
        projects = request.env['project.project'].sudo().search(
            []).filtered(
            lambda p: request.env.user.partner_id.id in p.message_follower_ids.mapped('partner_id').ids)
        # for project in projects:
        #     searchbar_filters.update({
        #         str(project.id): {'label': project.name, 'domain': [('project_id', '=', project.id)]}
        #     })

        # extends filterby criteria with company the customer has access to
        for company in request.env.user.company_ids:
            searchbar_filters.update({
                str(company.id): {'label': 'Company - ' + company.name, 'domain': [('company_id', '=', company.id)]}
            })

        # extends filterby criteria with project (criteria name is the project id)
        # Note: portal users can't view projects they don't follow
        # project_groups = request.env['account.analytic.line'].with_user(
        #     request.env.ref('base.user_admin').id).read_group([('project_id', 'not in', projects.ids)],
        #                                                       ['project_id'], ['project_id'])
        # for group in project_groups:
        #     proj_id = group['project_id'][0] if group['project_id'] else False
        #     proj_name = group['project_id'][1] if group['project_id'] else _('Others')
        #     searchbar_filters.update({
        #         str(proj_id): {'label': proj_name, 'domain': [('project_id', '=', proj_id)]}
        #     })

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Description')},
            'project': {'input': 'project', 'label': _('Search in Projects')},
            'task': {'input': 'task', 'label': _('Search in Tasks')},
            'employee': {'input': 'employee', 'label': _('Search in Employees')},
            'date': {'input': 'date', 'label': _('Search by Date')},
            'company': {'input': 'company', 'label': _('Search by Company')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'project': {'input': 'project', 'label': _('Project')},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        order = sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = str(request.env.user.company_id.id)
        domain = searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'date'
        archive_groups = self._get_archive_groups('project.task', domain)
        if date:
            domain += [('date', '>', date)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('project', 'all'):
                search_domain = OR([search_domain, [('project_id.name', 'ilike', search)]])
            if search_in in ('company', 'all'):
                search_domain = OR([search_domain, [('company_id.name', 'ilike', search)]])
            if search_in in ('task', 'all'):
                search_domain = OR([search_domain, [('task_id.name', 'ilike', search)]])
            if search_in in ('employee', 'all'):
                search_domain = OR([search_domain, [('employee_id.name', 'ilike', search)]])
            if search_in in ('date', 'all'):
                search_domain = OR([search_domain, [('date', 'ilike', search)]])
            domain += search_domain

        # if not request.env.user.has_group('bi_timesheet_portal.group_employee_timesheet_manager_portal'):
        if employee:
            domain += ['|', ('employee_id', '=', employee.id), ('employee_id.parent_id', '=', employee.id)]
        else:
            domain += [('employee_id', '=', False)]

        # timesheet for followed projects only
        domain += [('project_id','in',projects.ids)]
        # count for pager
        timesheets_count = timesheets_obj.sudo().search_count(domain)

        # pager
        pager = portal_pager(
            url="/my/timesheets",
            url_args={'date': date, 'sortby': sortby, 'filterby': filterby,
                      'search_in': search_in, 'search': search},
            total=timesheets_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        if groupby == 'project':
            order = "project_id, %s" % order  # force sort on project first to group by project in view
        tsheets = request.env['account.analytic.line'].sudo().search(domain,
                                                                                                               order=order,
                                                                                                               limit=self._items_per_page,
                                                                                                               offset=(
                                                                                                                              page - 1) * self._items_per_page)

        if groupby == 'project':
            grouped_timesheets = [request.env['account.analytic.line'].concat(*g) for k, g in
                                  groupbyelem(tsheets, itemgetter('project_id'))]
        else:
            grouped_timesheets = [tsheets]

        # content according to pager and archive selected
        timesheets = timesheets_obj.sudo().search(domain, order=order,
                                                                                            limit=self._items_per_page,
                                                                                            offset=pager['offset'])
        values.update({
            'timesheets': timesheets,
            'page_name': 'timesheets',
            'pager': pager,
            'searchbar_sortings': sortings,
            'sortby': sortby,
            'default_url': '/my/timesheets',

            'date': date,
            'date_end': date,
            'grouped_timesheets': grouped_timesheets,
            'archive_groups': archive_groups,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("bi_timesheet_portal.display_timesheet_requests", values)

    @http.route(['/my/timesheets/<int:timesheet_id>'], type='http', auth="public", website=True)
    def portal_timesheet_page(self, timesheet_id, report_type=None, access_token=None, message=False, download=False,
                              **kw):

        if timesheet_id:
            timesheet_sudo = request.env['account.analytic.line'].sudo().browse([timesheet_id])
        else:
            return request.redirect('/my/timesheets')

        # use sudo to allow accessing/viewing requests for public user
        values = {
        }
        values.update({
            'timesheet_request': timesheet_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/my/timesheets',
            'bootstrap_formatting': True,
        })

        return request.render('bi_timesheet_portal.display_timesheet_request', values)

    @http.route(['/timesheet_request_form'], type='http', auth="user", website=True)
    def portal_timesheet_request_form(self, **kw):
        if not request.env.user.has_group(
                'bi_timesheet_portal.group_employee_timesheet_portal') and not request.env.user.has_group(
            'bi_timesheet_portal.group_employee_timesheet_manager_portal'):
            return request.render("bi_timesheet_portal.not_allowed_timesheet_request")
        values = {}
        projects = request.env['project.project'].sudo().search([]).filtered(
            lambda p: request.env.user.partner_id.id in p.message_follower_ids.mapped('partner_id').ids)
        tasks = request.env['project.task'].sudo().search(
            [('project_id', 'in', projects.ids)])
        employees = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)])
        values.update({
            'projects': projects,
            'companies': request.env.user.company_ids,
            'employees': employees,
            'tasks': tasks,
            'error_fields': '',
        })
        return request.render("bi_timesheet_portal.timesheet_request_submit", values)

    @http.route(['/timesheet_request_submit/'], type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def portal_timesheet_request_submit(self, **kw):
        vals = request.params.copy()
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
        if request.params.get('task_id', False):
            task_id = int(request.params.get('task_id'))
            vals.update({
                'task_id': task_id,
            })

        if request.params.get('employee_id', False):
            employee_id = int(request.params.get('employee_id'))
            vals.update({
                'employee_id': employee_id,
            })

        if request.params.get('unit_amount', False):
            unit_amount = float(request.params.get('unit_amount'))
            minute, hour = math.modf(unit_amount)
            hour = int(hour)
            minute = round(minute, 2) * 100 / 60
            formatted_time = hour + minute
            vals.update({
                'unit_amount': formatted_time,
            })

        date = request.params.get('date')
        vals.update({
            'date': datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) if date else False,
        })
        created_request = False
        try:
            created_request = request.env['account.analytic.line'].sudo().create(vals)

        except Exception as e:
            if created_request:
                created_request.sudo().unlink()
            values = {}
            projects = request.env['project.project'].sudo().search(
                []).filtered(
                lambda p: request.env.user.partner_id.id in p.message_follower_ids.mapped('partner_id').ids)

            tasks = request.env['project.task'].sudo().search([])
            employees = request.env['hr.employee'].sudo().search(
                [('user_id', '=', request.env.user.id)])
            values.update({
                'projects': projects,
                'employees': employees,
                'companies': request.env.user.company_ids,
                'tasks': tasks,
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("bi_timesheet_portal.timesheet_request_submit", values)

        return request.render("bi_timesheet_portal.thankyou_page")

    @http.route(['/timesheet_delete'], type='http', auth="user", website=True)
    def portal_delete_timesheet(self, **kw):
        timesheet_id = request.params.get('id')
        if timesheet_id:
            timesheet = request.env['account.analytic.line'].sudo().search(
                [('id', '=', int(timesheet_id))])
            if timesheet:
                try:
                    timesheet.sudo().unlink()
                except:
                    pass
        return request.redirect('/my/timesheets')

    @http.route(['/timesheet/project_infos/'], type='json', auth="public", methods=['POST'], website=True)
    def project_infos(self, project, **kw):
        tasks = []
        if project:
            project = request.env['project.project'].sudo().search(
                [('id', '=', project)])
            tasks = [(task.id, task.display_name) for task in project.sudo().task_ids]
        return dict(
            tasks=tasks,
        )

    @http.route(['/timesheet/company_info/'], type='json', auth="public", methods=['POST'], website=True)
    def company_info(self, company, **kw):
        projects = []
        if company:
            project_ids = request.env['project.project'].sudo().search(
                []).filtered(
            lambda p: request.env.user.partner_id.id in p.message_follower_ids.mapped('partner_id').ids)
            for project in project_ids:
                if project.company_id.id == int(company):
                    projects.append((project.id, project.display_name))
        return dict(
            projects=projects,
        )
