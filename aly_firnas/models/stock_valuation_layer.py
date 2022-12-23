# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    move_location_dest_id = fields.Many2one('stock.location', "Destination Location",
                                            related='stock_move_id.location_dest_id', store=True)
    move_warehouse_id = fields.Many2one('stock.warehouse', "Destination Location",
                                        related='move_location_dest_id.warehouse_id',
                                        store=True)
