# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order.line'

    reinvoiced = fields.Boolean(string="Re-Invoiced")
