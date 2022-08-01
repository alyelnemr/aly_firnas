# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    description = fields.Char('Description', readonly=True)

    @api.onchange('lot_id')
    def change_calibration_date(self):
        if self.lot_id:
            self.description = self.lot_id.note
        else:
            self.description = False
