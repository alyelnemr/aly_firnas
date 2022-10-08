# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class AnalyticAccountTagInherit(models.Model):
    _inherit = 'account.analytic.tag'

    @api.model
    def create(self, vals):
        has_my_group = self.env.user.has_group('bi_security_creation.group_create_analytic_tags')
        if not has_my_group and not self.env.su:
            raise exceptions.ValidationError("Sorry you can't create analytic tags!")
        return super(AnalyticAccountTagInherit, self).create(vals)

    
    def write(self, vals):
        has_my_group = self.env.user.has_group('bi_security_creation.group_create_analytic_tags')
        if not has_my_group and not self.env.su:
            raise exceptions.ValidationError("Sorry you can't edit analytic tags!")
        return super(AnalyticAccountTagInherit, self).write(vals)
