# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user, domain=[])
