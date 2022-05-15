# -*- coding: utf-8 -*-

import math
import json
from odoo import http, _, fields
from odoo.http import request
from datetime import datetime, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
# from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager

import math
from collections import namedtuple
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT
from collections import OrderedDict

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _onchange_request_parameters
DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')



HOURS = [
        ('0', '12:00 PM'), ('0.5', '0:30 AM'),
        ('1', '1:00 AM'), ('1.5', '1:30 AM'),
        ('2', '2:00 AM'), ('2.5', '2:30 AM'),
        ('3', '3:00 AM'), ('3.5', '3:30 AM'),
        ('4', '4:00 AM'), ('4.5', '4:30 AM'),
        ('5', '5:00 AM'), ('5.5', '5:30 AM'),
        ('6', '6:00 AM'), ('6.5', '6:30 AM'),
        ('7', '7:00 AM'), ('7.5', '7:30 AM'),
        ('8', '8:00 AM'), ('8.5', '8:30 AM'),
        ('9', '9:00 AM'), ('9.5', '9:30 AM'),
        ('10', '10:00 AM'), ('10.5', '10:30 AM'),
        ('11', '11:00 AM'), ('11.5', '11:30 AM'),
        ('12', '12:00 AM'), ('12.5', '0:30 PM'),
        ('13', '1:00 PM'), ('13.5', '1:30 PM'),
        ('14', '2:00 PM'), ('14.5', '2:30 PM'),
        ('15', '3:00 PM'), ('15.5', '3:30 PM'),
        ('16', '4:00 PM'), ('16.5', '4:30 PM'),
        ('17', '5:00 PM'), ('17.5', '5:30 PM'),
        ('18', '6:00 PM'), ('18.5', '6:30 PM'),
        ('19', '7:00 PM'), ('19.5', '7:30 PM'),
        ('20', '8:00 PM'), ('20.5', '8:30 PM'),
        ('21', '9:00 PM'), ('21.5', '9:30 PM'),
        ('22', '10:00 PM'), ('22.5', '10:30 PM'),
        ('23', '11:00 PM'), ('23.5', '11:30 PM')]


class CustomerPortal(CustomerPortal):


    def check_approval_update(self, holiday):
        if holiday.state == 'confirm' and holiday.holiday_status_id.validation_type == 'both':
            return self._check_approval_update(holiday, 'validate1')
        else:
            return self._check_approval_update(holiday, 'validate')


    def _check_approval_update(self, holiday, state):
        # """ Check if target state is achievable. """
        current_employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)], limit=1)
        is_officer = request.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = request.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        # for holiday in self:
        val_type = holiday.holiday_status_id.validation_type

        if not is_manager and state != 'confirm':
            if state == 'draft':
                if holiday.state == 'refuse':
                    return False
                if holiday.date_from.date() <= fields.Date.today():
                    return False
                if holiday.employee_id != current_employee:
                    return False
            else:
                if val_type == 'no_validation' and current_employee == holiday.employee_id:
                    return True

                # This handles states validate1 validate and refuse
                if holiday.employee_id == current_employee:
                    return False

                if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                    if not is_officer and request.env.user != holiday.employee_id.leave_manager_id:
                        return False
        return True

    
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        holidays = request.env['hr.leave']

        if request.env.user.has_group('odoo_leave_request_portal_employee.group_employee_leave_manager'):
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            if employee:
                holidays_count = holidays.sudo().search_count(['|', ('user_id', 'child_of', [request.env.user.id]),
                          ('employee_id.parent_id', '=', employee.id)])
            else:
                holidays_count = holidays.sudo().search_count([])
        else:
            holidays_count = holidays.sudo().search_count([
            ('user_id', 'child_of', [request.env.user.id]),
            # ('type','=','remove')
              ])

        values.update({
            'holidays_count': holidays_count,
            'employee_data': employee,
        })
        return values
    
    @http.route(['/my/leave_request', '/my/leave_request/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_leave_request(self, page=1, date=None, sortby=None, filterby=None, search=None,
                                     search_in='employee', groupby='none', **kw):
        if not request.env.user.has_group('odoo_leave_request_portal_employee.group_employee_leave') and not request.env.user.has_group('odoo_leave_request_portal_employee.group_employee_leave_manager'):
            # return request.render("odoo_timesheet_portal_user_employee.not_allowed_leave_request")
            return request.render("odoo_leave_request_portal_employee.not_allowed_leave_request")
        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        holidays_obj = http.request.env['hr.leave']

        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)

        sortings = {
            'date': {'label': _('Newest'), 'order': 'date_from desc'},
            'name': {'label': _('Description'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
            'employee_id': {'label': _('Employee'), 'order': 'employee_id'},
        }

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        for company in request.env.user.company_ids:
            searchbar_filters.update({
                str(company.id): {'label': company.name, 'domain': [('mode_company_id', '=', company.id)]}
            })
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Description')},
            'employee': {'input': 'employee', 'label': _('Search in Employees')},
            'date': {'input': 'date', 'label': _('Search by Date')},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'employee': {'input': 'employee', 'label': _('Employee')},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        order = sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = str(request.env.user.company_id.id)

        domain = searchbar_filters[filterby]['domain']

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('employee', 'all'):
                search_domain = OR([search_domain, [('employee_id.name', 'ilike', search)]])
            if search_in in ('date', 'all'):
                search = search.replace("/", "-")
                search_text = search.split()
                if len(search_text):
                    search_date = search_text[0].split('-')
                    if len(search_date) == 3:
                        search_date = '%s-%s-%s' % (search_date[2], search_date[1], search_date[0])
                        search_domain = OR([search_domain, [('request_date_from', 'ilike', search_date)]])
                    elif len(search_date) == 2:
                        search_date = '%s-%s' % (search_date[1], search_date[0])
                        search_domain = OR([search_domain, [('request_date_from', 'ilike', search_date)]])
                search_domain = OR([search_domain, [('date_from', 'ilike', search)]])
            domain += search_domain
        
        order = sortings.get(sortby, sortings['date'])['order']

        if request.env.user.has_group('odoo_leave_request_portal_employee.group_employee_leave_manager'):
            if employee:
                domain += ['|', '|', ('user_id', 'child_of', [request.env.user.id]), ('employee_id.parent_id', '=', employee.id), ('employee_id', '=', employee.id)]
        else:
            if employee:
                domain += [
                    '|',
                    ('user_id', 'child_of', [request.env.user.id]),
                    ('employee_id', '=', employee.id)
                ]
            else:
                domain += [
                    ('user_id', 'child_of', [request.env.user.id]),
                    # ('type','=','remove')
                ]

        # count for pager
        holidays_count = http.request.env['hr.leave'].sudo().search_count(domain)
        # pager
        # pager = request.website.pager(
        pager = portal_pager(
            url="/my/leave_request",
            total=holidays_count,
            page=page,
            step=self._items_per_page,
            url_args={'date': date, 'sortby': sortby, 'filterby': filterby,
                      'search_in': search_in, 'search': search},
        )
        
        # content according to pager and archive selected
        holidays = holidays_obj.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        holidays_balance = {}
        for holiday in holidays:
            if holiday.holiday_status_id.allocation_type != 'no':
                data_days = holiday.holiday_status_id.get_days_leave(holiday.employee_id.id, holiday)
                result = data_days.get(holiday.holiday_status_id.id, {})
                max_leaves = result.get('max_leaves', 0)
                virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
                holidays_balance[holiday.id] = _('%g remaining out of %g') % (float_round(virtual_remaining_leaves, precision_digits=2) or 0.0, float_round(max_leaves, precision_digits=2) or 0.0)
            else:
                holidays_balance[holiday.id] = _('No allocation')

        if groupby == 'employee':
            grouped_holidays = [request.env['hr.leave'].concat(*g) for k, g in
                                  groupbyelem(holidays, itemgetter('employee_id'))]
        else:
            grouped_holidays = [holidays]
        values.update({
            'holidays': holidays,
            'holidays_balance': holidays_balance,
            'page_name': 'holidays',
            'sortings' : sortings,
            'sortby': sortby,
            'pager': pager,
            'default_url': '/my/leave_request',
            'check_approval_update': self.check_approval_update,
            'searchbar_sortings': sortings,
            'date': date,
            'date_end': date,
            'grouped_holidays': grouped_holidays,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'search': search,
        })
        return request.render("odoo_leave_request_portal_employee.display_leave_request", values)


    @http.route(['/leave_request_form'], type='http', auth="user", website=True)
    def portal_leave_request_form(self, **kw):
        if not request.env.user.has_group(
                'odoo_leave_request_portal_employee.group_employee_leave') and not request.env.user.has_group(
                'odoo_leave_request_portal_employee.group_employee_leave_manager'):
            return request.render("odoo_leave_request_portal_employee.not_allowed_leave_request")
        values = {}
        leave_types = request.env['hr.leave.type'].sudo().search([])
        employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
        values.update({
            'companies': request.env.user.company_ids,
            'leave_types': leave_types,
            'employees': employees,
            'hours': HOURS,
            'error_fields': '',
        })
        return request.render("odoo_leave_request_portal_employee.leave_request_submit", values)



    ###################################
    ###  leaves validations/onchanges
    ###################################

    def _check_date(self, vals):
        if vals.get('date_from', False) and vals.get('date_to', False) and vals.get('employee_id', False):
            domain = [
                ('date_from', '<=', vals.get('date_to')),
                ('date_to', '>', vals.get('date_from')),
                ('employee_id', '=', vals.get('employee_id')),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = request.env['hr.leave'].sudo().search_count(domain)
            if nholidays:
                raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

            if vals.get('date_from') > vals.get('date_to'):
                raise ValidationError(_('The start date must be anterior to the end date.'))

    def _check_holidays(self, vals):
        holiday_status_id = vals.get('holiday_status_id', False)
        if holiday_status_id:
            holiday_status_id = request.env['hr.leave.type'].sudo().browse([holiday_status_id])
            if vals.get('employee_id', False) and holiday_status_id and holiday_status_id.allocation_type != 'no':
                leave_days = holiday_status_id.get_days(vals.get('employee_id'))[holiday_status_id.id]
                if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                                float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                            'Please also check the leaves waiting for validation.'))

    def _check_leave_type_validity(self, vals):
        if vals.get('holiday_status_id', False):
            holiday_status_id = request.env['hr.leave.type'].sudo().browse([vals.get('holiday_status_id')])
            if holiday_status_id.validity_start and holiday_status_id.validity_stop:
                vstart = holiday_status_id.validity_start
                vstop = holiday_status_id.validity_stop
                dfrom = vals.get('date_from', False)
                dto = vals.get('date_to', False)
                if dfrom and dto and (dfrom.date() < vstart or dto.date() > vstop):
                    raise UserError(
                        _('You can take %s only between %s and %s') % (
                            holiday_status_id.display_name, holiday_status_id.validity_start,
                            holiday_status_id.validity_stop))
        else:
            raise UserError(_('Please select leave type'))


    def _onchange_request_parameters(self, vals):
        if not vals.get('request_date_from', False):
            vals.update({'date_from': False})
            return vals

        if vals.get('request_unit_half', False):
            vals.update({'request_date_to': vals.get('request_date_from')})

        if not vals.get('request_date_to', False):
            vals.update({'date_to': False})
            return vals

        employee_id = False
        if vals.get('employee_id', False):
            employee_id = request.env['hr.employee'].sudo().browse(
                [vals.get('employee_id')])

        resource_calendar_id = employee_id.resource_calendar_id or request.env.company.resource_calendar_id
        domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
        attendances = request.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

        # Must be sorted by dayofweek ASC and day_period DESC
        attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

        default_value = DummyAttendance(0, 0, 0, 'morning', False)

        if resource_calendar_id.two_weeks_calendar:
            # find week type of start_date
            start_week_type = int(math.floor((vals.get('request_date_from').toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
            # First, add days of actual week coming after date_from
            attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= vals.get('request_date_from').weekday()]
            # Second, add days of the other type of week
            attendance_filtred += list(attendance_actual_next_week)
            # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
            attendance_filtred += list(attendance_actual_week)

            end_week_type = int(math.floor((vals.get('request_date_to').toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
            attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= vals.get('request_date_to').weekday()]))
            attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
            attendance_filtred_reversed += list(reversed(attendance_actual_week))

            # find first attendance coming after first_day
            attendance_from = attendance_filtred[0]
            # find last attendance coming before last_day
            attendance_to = attendance_filtred_reversed[0]
        else:
            # find first attendance coming after first_day
            attendance_from = next((att for att in attendances if int(att.dayofweek) >= vals.get('request_date_from').weekday()), attendances[0] if attendances else default_value)
            # find last attendance coming before last_day
            attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= vals.get('request_date_to').weekday()), attendances[-1] if attendances else default_value)

        if vals.get('request_unit_half', False):
            if vals.get('request_date_from_period', False) == 'am':
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_from.hour_to)
            else:
                hour_from = float_to_time(attendance_to.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
        elif vals.get('request_unit_hours', False):
            hour_from = float_to_time(float(vals.get('request_hour_from', 0)))
            hour_to = float_to_time(float(vals.get('request_hour_to', 0)))
        elif vals.get('request_unit_custom', False):
            hour_from = vals.get('date_from').time()
            hour_to = vals.get('date_to').time()
        else:
            hour_from = float_to_time(attendance_from.hour_from)
            hour_to = float_to_time(attendance_to.hour_to)

        tz = request.env.user.tz if request.env.user.tz else 'UTC'  # custom -> already in UTC
        date_from = timezone(tz).localize(datetime.combine(vals.get('request_date_from'), hour_from)).astimezone(
            UTC).replace(tzinfo=None)
        date_to = timezone(tz).localize(datetime.combine(vals.get('request_date_to'), hour_to)).astimezone(UTC).replace(
            tzinfo=None)
        vals.update({'date_from': date_from})
        vals.update({'date_to': date_to})
        vals = self._onchange_leave_dates(vals)
        return vals

    def _onchange_request_unit_half(self, vals):
        if vals.get('request_unit_half', False):
            vals.update({
                'request_unit_hours': False,
                'request_unit_custom': False
            })
        vals = self._onchange_request_parameters(vals)
        return vals

    def _onchange_employee_id(self, vals):
        if vals.get('employee_id', False):
            employee_id = request.env['hr.employee'].sudo().browse([vals.get('employee_id')])
            if employee_id:
                vals.update({
                    'manager_id': employee_id.parent_id.id if employee_id.parent_id else False,
                    'department_id': employee_id.department_id.id
                })
        return vals

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = request.env['hr.employee'].browse(employee_id)
            return employee._get_work_days_data(date_from, date_to)

        today_hours = request.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        hours = request.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)

        return {'days': hours / (today_hours or HOURS_PER_DAY), 'hours': hours}

    def _onchange_leave_dates(self, vals):
        if vals.get('date_from', False) and vals.get('date_to', False):
            number_of_days = self._get_number_of_days(vals.get('date_from'), vals.get('date_to'), vals.get('employee_id', False))['days']
        else:
            number_of_days = 0
        vals.update({
            'number_of_days': number_of_days,
        })
        return vals


    @http.route(['/leave_request_submit/'], type='http', auth="user", website=True)
    def portal_leave_request_submit(self, **kw):
        vals = {}
        if request.params.get('leave_type', False):
            leave_type_id = int(request.params.get('leave_type'))
            vals.update({
                'holiday_status_id': leave_type_id,
            })
        if request.params.get('company_id', False):
            mode_company_id = int(request.params.get('company_id'))
            vals.update({
                'mode_company_id': mode_company_id or False,
            })
        if request.params.get('employee_id', False):
            employee_id = int(request.params.get('employee_id'))
            vals.update({
                'employee_id': employee_id,
            })
        if request.params.get('half_day', False):
            half_day = True
            vals.update({
                'request_unit_half': half_day,
            })
        if request.params.get('description', False):
            description = request.params.get('description')
            vals.update({
                'name': description,
            })

        date_from = request.params.get('date_from')
        vals.update({
            'request_date_from': datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) if date_from else False,
        })
        date_to = request.params.get('date_to')
        vals.update({
            'request_date_to': datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT) if date_to else False,
        })

        if request.params.get('request_unit_hours', False):
            vals.update({
                'request_hour_from': request.params.get('request_hour_from'),
                'request_hour_to': request.params.get('request_hour_to'),
                'request_unit_hours': request.params.get('request_unit_hours'),
                'request_date_to': vals.get('request_date_from'),
            })

        created_leave = False
        try:
            vals = self._onchange_request_parameters(vals)
            vals = self._onchange_request_unit_half(vals)
            vals = self._onchange_employee_id(vals)
            vals = self._onchange_leave_dates(vals)

            self._check_date(vals)
            self._check_holidays(vals)
            self._check_leave_type_validity(vals)

            created_leave = request.env['hr.leave'].sudo().create(vals)

        except Exception as e:
            if created_leave:
                created_leave.unlink()
            values = {}
            leave_types = request.env['hr.leave.type'].sudo().search([])
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)])
            values.update({
                'leave_types': leave_types,
                'employees': employees,
                'companies': request.env.user.company_ids,
                'hours': HOURS,
                'error_fields': json.dumps(e.args[0]),
            })
            return request.render("odoo_leave_request_portal_employee.leave_request_submit", values)

        return request.redirect('/my/leave_request')


    @http.route(['/leave_approve'], type='http', auth="user", website=True)
    def portal_approve_leave_request(self, **kw):
        leave_id = request.params.get('id')
        if leave_id:
            holiday = request.env['hr.leave'].sudo().search([('id', '=', int(leave_id))])
            if holiday:
                try:
                    holiday.action_approve() if holiday.state == 'confirm' else holiday.action_validate()
                except:
                    pass
        return request.redirect('/my/leave_request')

    @http.route(['/leave_confirm'], type='http', auth="user", website=True)
    def portal_confirm_leave_request(self, **kw):
        leave_id = request.params.get('id')
        if leave_id:
            holiday = request.env['hr.leave'].sudo().search(
                [('id', '=', int(leave_id))])
            if holiday:
                try:
                    holiday.action_confirm()
                except:
                    pass
        return request.redirect('/my/leave_request')

    @http.route(['/leave_delete'], type='http', auth="user", website=True)
    def portal_delete_leave_request(self, **kw):
        leave_id = request.params.get('id')
        if leave_id:
            holiday = request.env['hr.leave'].sudo().search(
                [('id', '=', int(leave_id))])
            if holiday:
                try:
                    if holiday.state == 'draft':
                        holiday.unlink()
                    else:
                        holiday.action_draft()
                        holiday.unlink()
                except:
                    pass
        return request.redirect('/my/leave_request')


    @http.route(['/leave_refuse'], type='http', auth="user", website=True)
    def portal_refuse_leave_request(self, **kw):
        leave_id = request.params.get('id')
        if leave_id:
            holiday = request.env['hr.leave'].sudo().search([('id', '=', int(leave_id))])
            if holiday:
                try:
                    holiday.action_refuse()
                    holiday.write({
                        'report_note': request.params.get('description') if request.params.get('description') else False
                    })
                except:
                    pass
        return request.redirect('/my/leave_request')

    @http.route(['/leave/leave_company_infos'], type='json', auth="public", methods=['POST'], website=True)
    def leave_company_infos(self, company, **kw):
        leave_types = []
        if company:
            leave_type_ids = request.env['hr.leave.type'].sudo().search(
                [('company_id', '=', int(company))])
            for type in leave_type_ids:
                leave_types.append((type.id, type.display_name))
        return dict(
            leave_types=leave_types,
        )