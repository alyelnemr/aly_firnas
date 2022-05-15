# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReinvoiceCustomerWizard(models.TransientModel):
    _name = 'reinvoice.customer.wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sales Order", required=True)
    purchase_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")

    def action_update_order_lines(self):
        self.ensure_one()
        if self.sale_order_id and self.purchase_line_id:
            purchase_line_id = self.purchase_line_id
            if not purchase_line_id.product_id.sale_ok:
                raise UserError(_('Product must can be sold'))
            sale_order_line_id = self.sale_order_id.order_line.sudo().create({
                'product_id': purchase_line_id.product_id.id,
                'product_uom_qty': purchase_line_id.product_qty,
                'order_id': self.sale_order_id.id,
                'reinvoiced': True
            })
            sale_order_line_id.sudo().product_id_change()
            sale_order_line_id.sudo().write({'price_unit': purchase_line_id.price_unit})
            purchase_line_id.sudo().write({'reinvoiced': True})
