# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    check_number = fields.Integer(string="Check Number")
