# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.quant'

    lot_description = fields.Html(string='Lot Description',related='lot_id.note', readonly=True)
    lot_ref = fields.Char(string='Lot Internal Reference',related='lot_id.ref', readonly=True)
