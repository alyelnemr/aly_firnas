# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_picking_default_values(self):
        return {
            'move_lines': [],
            'picking_type_id': self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id,
            'state': 'draft',
            'return_picking_of_picking_id': self.picking_id.id,
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id
        }
