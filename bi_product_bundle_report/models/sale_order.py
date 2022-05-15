# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero
import textile


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_additional_ids = fields.One2many(
        'sale.order.additional', 'order_id', 'Additional Products Lines',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    show_component_price = fields.Boolean(string="Show Component Price", default=False)

    split_page = fields.Boolean(string='Split Page?')

    def print_bundled_quotation(self):
        self.ensure_one()
        order_lines = self.order_line
        data = {}

        sections = order_lines.mapped('section')
        for section in sections:
            data[str(section.id)] = {
                'name': section.name,
                'total_price': sum([
                    (ol.price_subtotal if not ol.product_id.child_line else ol.price_unit * ol.product_uom_qty) for ol in
                    order_lines.filtered(lambda l: l.section.id == section.id)
                ]),
                'lines': [{
                    'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                            + ol.product_id.name,
                    'desc': textile.textile(ol.name) if ol.name else '',
                    'qty': int(ol.product_uom_qty),
                    'total_price': ol.item_price if not float_is_zero(ol.item_price,
                                                                      precision_rounding=2) else ol.price_subtotal,
                    'sub_lines': ol.get_orderline_sublines()
                } for ol
                    in order_lines.filtered(lambda l: l.section.id == section.id and not self.is_sub_product(l))]
                    
            }
            # and l.bundle_status in ('bundle','bundel_of_bundle')
        return data

    def is_sub_product(self,line):
        return self.order_line.filtered(lambda l:l.id == line.parent_order_line.id)
    
    def is_updated_bundle(self,line):
        return line.get_orderline_sublines()

    def get_optional_lines(self):
        self.ensure_one()
        order_lines = self.sale_order_option_ids
        data = {}

        sections = order_lines.mapped('section')
        for section in sections:
            data[str(section.id)] = {
                'name': section.name,
                'lines': [
                    {
                        'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                                + ol.product_id.name,
                        'desc': textile.textile(
                            ol.name) if ol.name else '',
                        'qty': int(ol.quantity),
                        'total_price': ol.quantity * ol.price_unit,
                        'price_note': ol.price_note,
                        'disc': str(ol.discount) + '%'
                    } for ol in
                    order_lines.filtered(lambda l: l.section.id == section.id)
                ]
            }
        return data

    def get_additional_lines(self):
        self.ensure_one()
        order_lines = self.sale_order_additional_ids
        data = {}

        sections = order_lines.mapped('section')
        for section in sections:
            data[str(section.id)] = {
                'name': section.name,
                'lines': [
                    {
                        'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                                + ol.product_id.name,
                        'desc': textile.textile(
                            ol.name) if ol.name else '',
                        'qty': int(ol.quantity),
                        'total_price': ol.quantity * ol.price_unit,
                        'price_note': ol.price_note,
                        'disc': str(ol.discount) + '%'
                    } for ol in
                    order_lines.filtered(lambda l: l.section.id == section.id)
                ]
            }
        return data
