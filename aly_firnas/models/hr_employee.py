# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class Employee(models.Model):
    _inherit = "hr.employee"

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
