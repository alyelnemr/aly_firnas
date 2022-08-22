# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class AnalyticAccountTagType(models.Model):
    _name = 'account.analytic.tag.type'

    name = fields.Char(string='Analytic Tag Type', required=True)


class AnalyticAccountTagInherit(models.Model):
    _inherit = 'account.analytic.tag'

    analytic_tag_type_id = fields.Many2one('account.analytic.tag.type', string='Analytic Tag Type')
    active = fields.Boolean(default=True, help="Set active to false to hide the Analytic Tag without removing it.")
