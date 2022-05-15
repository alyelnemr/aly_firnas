# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BankStatementAccountInherit(models.Model):
    _inherit = 'account.bank.statement'

    check_number = fields.Integer(string="Check Number")
