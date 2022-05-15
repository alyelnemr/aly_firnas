# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockProductionLOT(models.Model):
    _inherit = 'stock.production.lot'

    is_fields_required = fields.Boolean(string="Dates Required?", compute="get_is_field_required")
    calibration_date = fields.Date(string="Calibration Date")
    serial_creation_date = fields.Date(string="Creation Date", default=fields.Date.context_today)

    def get_is_field_required(self):
        for record in self:
            record.is_fields_required = (record.product_id.tracking == 'serial' and record.product_id.is_required)

    @api.model
    def create(self, vals):
        product_id = self._context.get('default_product_id')
        if not product_id and 'product_id' in vals:
            product_id = vals['product_id']
        product = self.env['product.product'].browse(product_id)
        if product.is_required \
                and 'calibration_date' not in vals \
                and not self._context.get('default_calibration_date', False):
            form_view_id = self.env.ref("product_expiry.view_move_form_expiry").id
            res = {
                'type': 'ir.actions.act_window',
                'name': 'Lot/Serial Number',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.production.lot',
                'views': [(form_view_id, 'form')],
                'target': 'new',
            }
        else:
            res = super(StockProductionLOT, self).create(vals)
        return res
