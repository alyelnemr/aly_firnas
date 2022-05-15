# -*- coding: utf-8 -*-

import datetime
import calendar
import time

from odoo import http, _
from odoo.http import request
# from datetime import datetime, timedelta
from datetime import date 
from odoo import models, fields, registry, SUPERUSER_ID
# from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import UserError, ValidationError
from collections import OrderedDict

class MyAttendance(http.Controller):


    def _check_validity_check_in_check_out(self, check_in, check_out):
        """ verifies if check_in is earlier than check_out. """
        if check_in and check_out:
            if check_out < check_in:
                raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))


    def _check_validity(self, check_in, check_out, employee_id):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        # we take the latest attendance before our check_in time and check it doesn't overlap with ours
        company_id = employee_id.company_id
        last_attendance_before_check_in = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id.id),
            ('company_id', '=', company_id.id),
            ('check_in', '<=', check_in),
        ], order='check_in desc', limit=1)
        if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > check_in:
            raise ValidationError(_(
                "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                 'empl_name': employee_id.name,
                                                 'datetime': fields.Datetime.to_string(
                                                     fields.Datetime.context_timestamp(request,
                                                                                       fields.Datetime.from_string(
                                                                                           check_in))),
                                             })

        if not check_out:
            # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
            no_check_out_attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id.id),
                ('company_id', '=', company_id.id),
                ('check_out', '=', False),
            ], order='check_in desc', limit=1)
            if no_check_out_attendances:
                raise ValidationError(_(
                    "Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                                                     'empl_name': employee_id.name,
                                                     'datetime': fields.Datetime.to_string(
                                                         fields.Datetime.context_timestamp(request,
                                                                                           fields.Datetime.from_string(
                                                                                               no_check_out_attendances.check_in))),
                                                 })
        else:
            # we verify that the latest attendance with check_in time before our check_out time
            # is the same as the one before our check_in time computed before, otherwise it overlaps
            last_attendance_before_check_out = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id.id),
                ('company_id', '=', company_id.id),
                ('check_in', '<', check_out),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                raise ValidationError(_(
                    "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                     'empl_name': employee_id.name,
                                                     'datetime': fields.Datetime.to_string(
                                                         fields.Datetime.context_timestamp(request,
                                                                                           fields.Datetime.from_string(
                                                                                               last_attendance_before_check_out.check_in))),
                                                 })

    
    @http.route(['/my/sign_in_attendance'], type='http', auth="user", website=True)
    def sign_in_attendace(self, **post):
        if not request.env.user.has_group('odoo_portal_attendance.portal_user_employee_attendance'):
            return request.render("odoo_portal_attendance.not_allowed_attendance")
        import datetime
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        check_in_datetime = datetime.datetime.now()
        check_in = check_in_datetime.strftime("%Y-%m-%d %H:%M:%S")
        if employee:
            vals = {
                    'employee_id': employee.id,
                    'company_id': employee.company_id.id,
                    'check_in': check_in,
                    'check_in_web':True,
                    }

            try:
                self._check_validity(check_in_datetime, False, employee)
            except Exception as e:
                return request.render('odoo_portal_attendance.sign_in_attendance', {'error': e})

            attendance = request.env['hr.attendance'].sudo().create(vals)
            values = {
                    'attendance':attendance,
                    'error': False
                }
        # return request.render('odoo_portal_attendance.sign_in_attendance', values)
            return request.render('odoo_portal_attendance.sign_in_attendance', values)

    @http.route(['/my/sign_out_attendance'], type='http', auth="user", website=True)
    def sign_out_attendace(self, **post):
        if not request.env.user.has_group('odoo_portal_attendance.portal_user_employee_attendance'):
            return request.render("odoo_portal_attendance.not_allowed_attendance")
        import datetime
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])

        no_check_out_attendances = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('company_id', '=', employee.company_id.id),
                    ('check_out', '=', False),
                ], limit=1)
        check_out_datetime = datetime.datetime.now()
        check_out = check_out_datetime.strftime("%Y-%m-%d  %H:%M:%S")

        try:
            self._check_validity(no_check_out_attendances[0].check_in, check_out_datetime, employee)
        except Exception as e:
            return request.render('odoo_portal_attendance.sign_in_attendance', {'error': e})

        attendance = no_check_out_attendances.sudo().write({'check_out':check_out})
        values = {
                    'attendance':attendance,
                    'error': False
                }
        return request.render('odoo_portal_attendance.sign_out_attendance', values)

# class website_account(website_account):
class CustomerPortal(CustomerPortal):
    
    @http.route()
    def account(self, **kw):
        import datetime
        response = super(CustomerPortal, self).account(**kw)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        attendance_obj = request.env['hr.attendance']
        
        attendance_count = attendance_obj.sudo().search_count(
            [('employee_id','=', employee.id),
             ])
        response.qcontext.update({
                'attendance_count': attendance_count,
        })
        return response


    def check_work_days(self, month_days, employee):
        if month_days:
            start = datetime.datetime.combine(month_days[0], datetime.time.min)
            end = datetime.datetime.combine(month_days[-1], datetime.time.max)

            work_days_list = employee.list_work_time_per_day(start, end)
            work_days = []
            for dt in work_days_list:
                work_days.append(dt[0])
            return work_days
        return month_days

    
    def _prepare_portal_layout_values(self):
        import datetime
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        attendance_obj = request.env['hr.attendance']

        now = datetime.datetime.now()
        year = now.year
        month = now.month
        num_days = calendar.monthrange(year, month)[1]
        month_days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]

        attendance_count = 0
        attendance_recs = {}
        if employee:
            attendance_count = attendance_obj.sudo().search_count(
                [('employee_id','=', employee.id),
                 ])

            month_days = self.check_work_days(month_days, employee)

            attendances = attendance_obj.sudo().search([
                ('employee_id', '=', employee.id),
                ('company_id', '=', employee.company_id.id),
                ('check_in_date', 'in', month_days),
             ])
            for att in attendances:
                if att.check_in_date:
                    attendance_recs[att.check_in_date] = att

        values.update({
            'attendance_count': attendance_count,
            'attendance_recs': attendance_recs,
            'month_days': month_days,
            'now_date': now.date(),
        })
        return values
    
    @http.route(['/my/attendances', '/my/attendances/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_attendances(self, page=1, sortby=None, filterby=None, **kw):
        if not request.env.user.has_group('odoo_portal_attendance.portal_user_employee_attendance'):
            return request.render("odoo_portal_attendance.not_allowed_attendance")
        import datetime
        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        attendance_obj = http.request.env['hr.attendance']
        
        domain = [
            ('employee_id', '=', employee.id),
        ]
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        for company in request.env.user.company_ids:
            searchbar_filters.update({
                str(company.id): {'label': company.name, 'domain': [('company_id', '=', company.id)]}
            })
        if not filterby:
            filterby = str(request.env.user.company_id.id)
        domain = searchbar_filters[filterby]['domain']

        # count for pager
        attendance_count = attendance_obj.sudo().search_count(domain)
        
        # pager
        # pager = request.website.pager(
        pager = portal_pager(
            url="/my/attendances",
            total=attendance_count,
            page=page,
            step=self._items_per_page
        )
        
        no_check_out_attendances = request.env['hr.attendance'].sudo().search([
                     ('employee_id', '=', employee.id),
                     ('company_id', '=', employee.company_id.id),
                     ('check_out', '=', False),
                 ])
        
        # content according to pager and archive selected
        
        attendances = attendance_obj.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'attendances': attendances,
            'no_check_out_attendances': no_check_out_attendances,
            'page_name': 'attendance',
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'pager': pager,
            'default_url': '/my/attendances',
        })
        return request.render("odoo_portal_attendance.display_attendances", values)