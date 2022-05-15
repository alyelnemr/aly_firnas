# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_update_qty_received(self):
        self.ensure_one()
        wizard = self.env.ref('bi_purchase_qty_received.purchase_qty_received_wizard_view').id
        return {
            'name': _("Update Received Qty"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'purchase.qty.received.wizard',
            'views': [(wizard, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_purchase_line_id': self.id, 'default_qty_received': self.qty_received}
        }
