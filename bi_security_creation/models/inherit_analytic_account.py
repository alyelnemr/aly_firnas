# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class AnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    @api.model
    def create(self, vals):
        has_my_group = True # self.env.user.has_group('bi_security_creation.group_create_analytic_account')
        if not has_my_group:
            raise exceptions.ValidationError("Sorry you can't create analytic accounts!")
        return super(AnalyticAccountInherit, self).create(vals)

    
    def write(self, vals):
        has_my_group = True # self.env.user.has_group('bi_security_creation.group_create_analytic_account')
        if not has_my_group:
            raise exceptions.ValidationError("Sorry you can't edit analytic accounts!")
        return super(AnalyticAccountInherit, self).write(vals)
