# -*- coding: utf-8 -*-


from odoo import fields, models, tools, api


class InheritResUsers(models.Model):
    _inherit = 'res.users'

    is_user_to_approve = fields.Boolean("Is User To Approve", default=False)
