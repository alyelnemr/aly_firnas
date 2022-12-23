# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.quant'

    lot_description = fields.Html(string='Lot Description', related='lot_id.note', readonly=True)
    lot_ref = fields.Char(string='Lot Internal Reference', related='lot_id.ref', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', related='location_id.warehouse_id', store=True, readonly=True)
