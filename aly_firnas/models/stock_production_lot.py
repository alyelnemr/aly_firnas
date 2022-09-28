# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductionLot(models.Model):
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
            res = super(ProductionLot, self).create(vals)
        return res

    def name_get(self):
        return [(item.id, '%s (%s)' % (item.name, item.ref) if item.ref else '%s' % item.name) for item in self]

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        domain = args + ['|', ('name', operator, name), ('ref', operator, name)]
        model_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(model_ids).with_user(name_get_uid))
