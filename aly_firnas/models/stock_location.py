# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockLocation(models.Model):
    _inherit = 'stock.location'

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', compute='_compute_warehouse_id', store=True)

    def _compute_warehouse_id(self):
        for location in self:
            warehouses = self.env['stock.warehouse'].search([])
            for wh in warehouses:
                location_ids = self.env['stock.location'].search([('location_id', 'child_of', wh.view_location_id.id)])
                if location.id in location_ids.ids:
                    location.warehouse_id = wh
                    break
