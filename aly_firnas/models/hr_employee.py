# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class MyEmployee(models.Model):
    _inherit = "hr.employee"

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    employee_code = fields.Char('Employee Code', required=False)

    @api.model
    def create(self, vals):
        employee = super(MyEmployee, self).create(vals)
        employee_code = vals.get('employee_code') or self.employee_code
        employee_name = vals.get('name') or self.name
        tag_name = employee_code + ' - ' + employee_name if employee_code else employee_name
        analytic_tag_exist = self.env['account.analytic.tag'].search([('name', '=', tag_name)])
        if not analytic_tag_exist:
            analytic_tag = self.env['account.analytic.tag'].create({'name': tag_name})
            employee.analytic_tag_ids = analytic_tag.ids
        return employee

    def write(self, vals):
        employee_code = vals.get('employee_code') or self.employee_code
        employee_name = vals.get('name') or self.name
        tag_name = employee_code + ' - ' + employee_name if employee_code else employee_name
        analytic_tag_exist = self.env['account.analytic.tag'].search([('name', '=', tag_name)])
        if not analytic_tag_exist:
            analytic_tag = self.env['account.analytic.tag'].create({'name': tag_name})
            vals.update({'analytic_tag_ids': analytic_tag.ids})
        res = super(MyEmployee, self).write(vals)
        return res


class Employee(models.Model):
    _inherit = "hr.employee.public"

    analytic_tag_ids = fields.Many2many('account.analytic.tag', readonly=True)
