# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BankStatementAccountInherit(models.Model):
    _inherit = 'account.bank.statement'

    check_number = fields.Integer(string="Check Number")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)

