# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseLinesTransferWizard(models.TransientModel):
    _name = 'purchase.lines.transfer.wizard'

    current_purchase_order_id = fields.Many2one('purchase.order', string='Current Purchase Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True,
                                        domain=[('state', '=', 'draft')])
    line_ids = fields.Many2many('purchase.line.wizard', string='Purchase Lines')

    select_all = fields.Boolean(string='Select All')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if self.select_all:
            for line in self.line_ids:
                line.selected = True
        else:
            for line in self.line_ids:
                line.selected = False

    def action_confirm(self):
        purchase_order = self.purchase_order_id
        selected_lines = self.line_ids.filtered(lambda l: l.selected).mapped('related_po_line')

        new_origins = selected_lines.filtered(lambda l: l.origin).mapped('origin')
        all_origins = []
        if purchase_order.origin:
            all_origins = purchase_order.origin.split(', ')

        if new_origins:
            for new_origin in new_origins:
                if new_origin not in all_origins:
                    all_origins.append(new_origin)

        origins = set(all_origins)
        if origins:
            purchase_order.write({
                'origin': ', '.join(sorted(origins))
            })

        for line in selected_lines:
            line.update({'order_id': self.purchase_order_id.id})

        self.current_purchase_order_id.reset_origins()


class PurchaseLineWizard(models.TransientModel):
    _name = 'purchase.line.wizard'

    related_po_line = fields.Many2one('purchase.order.line', string='Purchase Lines')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Name')
    order_id = fields.Many2one('purchase.order', string='Order Reference')
    order_state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status')
    selected = fields.Boolean(string='Selected')
