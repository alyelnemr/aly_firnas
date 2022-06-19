# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployeeInherit(models.AbstractModel):
    _inherit = 'hr.employee.base'

    emergency_contact = fields.Char("Emergency Contact 1", groups="hr.group_hr_user")
    second_emergency_contact = fields.Char("Emergency Contact 2", groups="hr.group_hr_user")
    third_emergency_contact = fields.Char("Emergency Contact 3", groups="hr.group_hr_user")
    first_emergency_phone = fields.Char("Emergency Phone 1", groups="hr.group_hr_user")
    second_emergency_phone = fields.Char("Emergency Phone 2", groups="hr.group_hr_user")
    third_emergency_phone = fields.Char("Emergency Phone 3", groups="hr.group_hr_user")
    emp_ar_name = fields.Char(string="Employee Arabic Name")
    medical_id_num = fields.Char(string="Medical Id Number")
    home_address = fields.Char(string="Home Address")
    personal_mail = fields.Char(string="Personal E-mail")
    personal_mobile = fields.Char(string="Personal Mobile")
    can_drive_a_car = fields.Selection([
        ('yes', 'YES'),
        ('no', 'NO'),
    ], string='Can drive a car')
    have_driving_license = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Have driving license')
    languages = fields.Many2one('res.lang', string="Language",)
