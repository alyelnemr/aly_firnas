# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    employee_id = fields.Many2one('hr.employee', string="Employee")
