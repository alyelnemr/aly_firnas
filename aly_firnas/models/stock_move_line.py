# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def default_get(self, fields):
        result = super(StockMoveLine, self).default_get(fields)
        if self._context.get('active_id') and self.picking_id and 'move_id' in result:
            move_line = self.env['stock.move'].browse(result['move_id'])

            if 'lot_description' in fields and move_line.description_picking:
                result['lot_description'] = move_line.description_picking

            if 'lot_ref' in fields and move_line.description_picking:
                result['lot_ref'] = move_line.description_picking
        return result

    lot_description = fields.Html(string='Lot Description',related='lot_id.note', readonly=True)
    lot_ref = fields.Char(string='Lot Internal Reference',related='lot_id.ref', readonly=True)
