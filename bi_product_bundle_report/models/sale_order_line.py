# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero
import textile


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    item_price = fields.Float(string="Item Price", compute="get_item_price")
    name = fields.Text(string='Description', required=False)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")

    def _get_values_to_add_to_order(self):
        self.ensure_one()
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'discount': self.discount,
            'section': self.section.id,
            'company_id': self.order_id.company_id.id,
        }

    def get_item_price(self):
        for record in self:
            order_lines = self.search([('parent_order_line', '=', record.id)])
            if order_lines:
                item_price = 0
                while order_lines:
                    item_price += sum([
                        (ol.price_subtotal if ol.price_subtotal != 0 else 0.0)
                        for ol in order_lines
                    ])
                    order_lines = self.search([('parent_order_line', 'in', order_lines.ids)])
                result = item_price + record.price_subtotal
            else:
                result = record.price_subtotal
            record.item_price = result

    @api.onchange('is_printed')
    def set_is_printed(self):
        self.ensure_one()
        line_id = self._origin.id
        order_lines = self.order_id.order_line.filtered(
            lambda x: x.parent_order_line and x.parent_order_line.id == line_id)
        order_lines.write({'is_printed': self.is_printed})

    def get_orderline_sublines(self):
        self.ensure_one()
        order_lines = self.order_id.order_line
        vals = [
            {
                'name': ('[%s] ' % sl.product_id.default_code if sl.product_id.default_code else '') +
                        sl.product_id.name,
                'desc': textile.textile(sl.name) if sl.name else '',
                # 'desc': textile.textile(sl.name.replace(sl.product_id.display_name, '')) if sl.name and sl.product_id else '',
                'qty': int(sl.product_uom_qty),
                'total_price': sl.price_subtotal,
                'item_price': sl.item_price,
                'show_price': sl.order_id.show_component_price,
                'sub_lines': sl.get_orderline_sublines() or False
            } for sl in order_lines.filtered(
                lambda x: x.parent_order_line and x.parent_order_line.id == self.id and x.is_printed is True 
            )
        ]
        return vals

    