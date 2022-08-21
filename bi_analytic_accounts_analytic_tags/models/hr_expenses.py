# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritExpenses(models.Model):
    _inherit = 'hr.expense'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True, required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True,
                                        states={'post': [('readonly', True)], 'done': [('readonly', True)]},
                                        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
