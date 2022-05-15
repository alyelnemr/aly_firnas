# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    calibration_date = fields.Date(string="Calibration Date")
    product_dates_required = fields.Boolean(string="bol", related="product_id.is_required")
    product_tracking = fields.Selection(string="sel", related="product_id.tracking")

    @api.onchange('lot_id')
    def change_calibration_date(self):
        if self.lot_id:
            self.calibration_date = self.lot_id.calibration_date
        else:
            self.calibration_date = False

    def _action_done(self):
        for record in self:
            if not record.lot_id:
                super(StockMoveLine, record.with_context(default_calibration_date=record.calibration_date))._action_done()
            else:
                super(StockMoveLine, record)._action_done()
