# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)
