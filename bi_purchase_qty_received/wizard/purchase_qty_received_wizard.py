# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseQtyReceivedWizard(models.TransientModel):
    _name = 'purchase.qty.received.wizard'

    qty_received = fields.Float(string="Received Qty", required=True)
    purchase_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line", required=True)

    def action_update_qty_received(self):
        self.ensure_one()
        if self.purchase_line_id:
            self.purchase_line_id.sudo().write({'qty_received': self.qty_received})
