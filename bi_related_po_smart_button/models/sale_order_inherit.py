# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders', default=False)
    # purchase_order_count = fields.Integer(string='Delivery Orders', compute='_compute_purchase_order_ids', default=0)
    purchase_order_counter = fields.Integer(string='Delivery Orders', compute='_compute_purchase_order_ids', default=0)

    @api.depends('partner_id', 'state')
    def _compute_purchase_order_ids(self):
        for record in self:
            try:
                orders = self.env['purchase.order'].sudo().search([('origin', 'ilike', record.name)])
                # record.purchase_order_ids = orders
                record.purchase_order_count = len(orders)
            except exceptions:
                record.purchase_order_ids = False
                record.purchase_order_count = 0

    def action_view_purchase_order(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        purchase_orders = self.mapped('purchase_order_ids')

        if len(purchase_orders) > 1:
            action['domain'] = [('id', 'in', purchase_orders.ids)]
        elif purchase_orders:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = purchase_orders.id

        return action

    def action_cancel(self):
        if any(po.state in ('purchase', 'done') for po in self.purchase_order_ids):
            raise exceptions.ValidationError("You can not cancel the SO that related to any confirmed RFQs!")

        for po in self.purchase_order_ids:
            po.button_cancel()

        return super(SaleOrder, self).action_cancel()
