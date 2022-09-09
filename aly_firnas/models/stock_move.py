# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def default_get(self, fields):
        result = super(StockMove, self).default_get(fields)
        if self._context.get('active_id') and self.picking_id and 'move_id' in result:
            move_line = self.env['stock.move'].browse(result['move_id'])

            if 'lot_description' in fields and move_line.description_picking:
                result['lot_description'] = move_line.description_picking

            if 'lot_ref' in fields and move_line.description_picking:
                result['lot_ref'] = move_line.description_picking
        return result

    lot_description = fields.Html(string='Lot Description', readonly=True)
    lot_ref = fields.Char(string='Lot Internal Reference', readonly=True)

    def _get_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.

        HACK: This is needed while https://github.com/odoo/odoo/pull/29983
        is not merged.
        """
        price_unit = False
        po_line = self.purchase_line_id.sudo()
        if po_line and self.product_id == po_line.product_id:
            price = po_line._get_discounted_price_unit()
            if price != po_line.price_unit:
                # Only change value if it's different
                price_unit = po_line.price_unit
                po_line.sudo().price_unit = price
        res = super()._get_price_unit()
        if price_unit:
            po_line.sudo().price_unit = price_unit
        return res
