# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    def _action_done(self):
        for record in self:
            if not record.lot_id:
                super(StockMoveLine, record.with_context(default_calibration_date=record.calibration_date))._action_done()
            else:
                super(StockMoveLine, record)._action_done()
