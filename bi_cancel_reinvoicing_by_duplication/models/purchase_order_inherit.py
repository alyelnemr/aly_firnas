# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    sale_line_id = fields.Many2one('sale.order.line', string="Origin Sale Item", index=True, copy=False)
