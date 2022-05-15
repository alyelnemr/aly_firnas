# -*- coding: utf-8 -*-

import pytz
from datetime import datetime, date, timedelta, time
from odoo import models, fields, api, exceptions, _
from odoo.tools import float_compare
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class HrAttendanceInherit(models.Model):
    _inherit = "hr.attendance"

    contract_id = fields.Many2one('hr.contract', compute='get_current_contract', string='Current Contract', store=1)
    working_schedule_id = fields.Many2one('resource.calendar', compute='get_current_working_schedule',
                                          string='Current Working Schedule', store=1)

    # check in/out hours with timezone
    employee_timezone = fields.Char(compute='calc_dates', string='Employee Timezone', store=1)
    check_in_date = fields.Date(compute='calc_dates', string='Check-In Date', store=1)
    check_in_time = fields.Float(compute='calc_dates', string='Check-In Time', store=1)

    # planned attendance policy
    planned_check_in_date = fields.Datetime(compute='compute_attendance_policy', string='Planned In', store=0)
    planned_check_in_time = fields.Float(compute='compute_attendance_policy', string='Planned Check In Time', store=0)
    total_delay_in = fields.Float(compute='compute_attendance_policy', string='Delay In (Hrs)', store=0)
    is_late = fields.Boolean(compute='compute_attendance_policy', string='Late', store=0)
    is_late_approved = fields.Boolean(string='Lateness Approved?')

    def approve_late(self):
        for rec in self:
            if rec.is_late:
                rec.is_late_approved = False if rec.is_late_approved else True


    @api.depends('employee_id', 'employee_id.contract_ids', 'employee_id.contract_ids.state')
    def get_current_contract(self):
        for rec in self:
            rec.contract_id = rec.employee_id.contract_id

    @api.depends('employee_id', 'contract_id', 'employee_id.resource_calendar_id', 'contract_id.resource_calendar_id')
    def get_current_working_schedule(self):
        for rec in self:
            rec.working_schedule_id = rec.contract_id.resource_calendar_id if rec.contract_id else rec.employee_id.resource_calendar_id


    @api.depends('employee_id', 'employee_id.tz', 'check_in', 'check_out', 'working_schedule_id',
                 'working_schedule_id.tz')
    def calc_dates(self):
        for rec in self:
            if rec.working_schedule_id:
                tz = rec.working_schedule_id.tz
            else:
                tz = rec.employee_id.tz or 'UTC'
            employee_tz = pytz.timezone(tz)
            rec.employee_timezone = employee_tz

            if rec.check_in:
                check_in_date = pytz.UTC.localize(rec.check_in).astimezone(employee_tz)
                rec.check_in_time = float(check_in_date.hour + check_in_date.minute / 60.0)
                rec.check_in_date = check_in_date.date()

            if rec.check_out:
                check_out_date = pytz.UTC.localize(rec.check_out).astimezone(employee_tz)
                rec.check_out_time = float(check_out_date.hour + check_out_date.minute / 60.0)
                rec.check_out_date = check_out_date.date()

    def compute_attendance_policy(self):
        for rec in self:
            rec.total_delay_in = 0.0
            rec.planned_check_in_time = False
            rec.planned_check_in_date = False
            rec.is_late = False
            if rec.working_schedule_id:
                calendar = rec.working_schedule_id
                tz = calendar.tz
                employee_tz = pytz.timezone(tz)
                if rec.check_in_date:
                    check_in_day_start = employee_tz.localize(datetime.combine(rec.check_in_date, time.min))
                    check_in_day_end = employee_tz.localize(datetime.combine(rec.check_in_date, time.max))

                    # get work intervals for check in date
                    work_intervals = calendar._work_intervals(check_in_day_start, check_in_day_end, resource=rec.employee_id.resource_id)
                    if work_intervals:
                        i = 0
                        for start, stop, meta in work_intervals:
                            # take the planned check in from the first working interval
                            if i == 0:
                                rec.planned_check_in_time = float(start.hour + start.minute / 60.0)
                                rec.planned_check_in_date = start.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)
                            i += 1

                        if rec.check_in > rec.planned_check_in_date:
                            from_datetime = pytz.utc.localize(rec.planned_check_in_date)
                            to_datetime = pytz.utc.localize(rec.check_in)
                            late_interval_with_leaves = calendar._work_intervals(from_datetime, to_datetime, resource=rec.employee_id.resource_id)
                            rec.total_delay_in = sum(
                                (stop - start).total_seconds() / 3600
                                for start, stop, meta in late_interval_with_leaves
                            )
                        else:
                            rec.total_delay_in = 0
                        if float_compare(rec.total_delay_in, 0.0, 5) > 0:
                            rec.is_late = True
                        else:
                            rec.is_late = False



class HrLateAttendanceApprove(models.TransientModel):
    _name = 'hr.late.attendance.approve'
    _description = "Wizard - Late Attendance Approve"


    def approve(self):
        atts = self._context.get('active_ids')
        att_ids = self.env['hr.attendance'].browse(atts).\
            filtered(lambda x: x.is_late_approved == False and x.is_late == True)
        if att_ids:
            att_ids.approve_late()
