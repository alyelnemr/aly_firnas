# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_transfer_lines(self):
        purchase_lines = self.order_line

        if any(line.order_state != 'draft' for line in purchase_lines):
            raise exceptions.ValidationError("You can only transfer the lines that in Draft status!")

        lines = [(0, 0, {
            'related_po_line': l.id,
            'product_id': l.product_id.id,
            'name': l.name,
            'order_id': l.order_id.id,
            'order_state': l.order_state,
        }) for l in purchase_lines]

        ctx = {
            'default_current_purchase_order_id': self.id,
            'default_line_ids': lines,
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer Purchase Lines',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'purchase.lines.transfer.wizard',
            'context': ctx
        }

    def reset_origins(self):
        all_origins = self.order_line.filtered(lambda l: l.origin).mapped('origin')
        origins = set(all_origins)
        self.write({
            'origin': ', '.join(sorted(origins))
        })


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    order_state = fields.Selection(related='order_id.state')
    origin = fields.Char(string='Origin')

    def action_transfer_purchase_lines(self):
        purchase_lines = self

        if any(line.order_state != 'draft' for line in purchase_lines):
            raise exceptions.ValidationError("You can only transfer the lines that in Draft status!")

        lines = [(0, 0, {
            'related_po_line': l.id,
            'product_id': l.product_id.id,
            'name': l.name,
            'order_id': l.order_id.id,
            'order_state': l.order_state,
        }) for l in purchase_lines]

        ctx = {
            'default_line_ids': lines,
            'default_select_all': True,
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer Purchase Lines',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'purchase.lines.transfer.wizard',
            'context': ctx
        }
