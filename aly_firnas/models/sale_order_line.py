# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round
import textile


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)
    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True, states={'sale': [('readonly', True)]})
    name = fields.Text(string='Description', required=True, states={'sale': [('readonly', True)]})
    item_price = fields.Float(string="Item Price", store=False, compute="get_item_price")
    name = fields.Text(string='Description', required=False)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    internal_notes = fields.Text(string='Internal Notes')
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})

    @api.onchange('product_id')
    def get_analytic_tags(self):
        for line in self:
            line.analytic_account_id = line.order_id.analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id
            line.analytic_tag_ids = line.order_id.analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['analytic_account_id'] = self.analytic_account_id.id
        res['analytic_tag_ids'] = self.analytic_tag_ids.ids
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id)
        res.update({
            "analytic_account_id": self.order_id.analytic_account_id.id,
            "analytic_tag_ids": self.order_id.analytic_tag_ids.ids,
            "is_origin_so": True,

        })
        return res

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        res = super()._purchase_service_prepare_line_values(
            purchase_order=purchase_order, quantity=quantity
        )
        # update PO with analytic_account and analytic_tags
        purchase_order.analytic_account_id = self.order_id.analytic_account_id.id
        purchase_order.analytic_tag_ids = self.order_id.analytic_tag_ids.ids
        res.update({
            "account_analytic_id": self.order_id.analytic_account_id.id,
            "analytic_tag_ids": self.order_id.analytic_tag_ids.ids,
            "is_origin_so": True,
        })

        return res

    def action_update_factor(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            custom_rate = self.order_id.custom_rate
            is_manual = self.order_id.is_manual
            if is_manual and custom_rate > 0:
                custom_rate = self.order_id.custom_rate
                line.price_unit *= custom_rate
            taxes = line.tax_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_uom_qty, product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))
        # if procurements:
        #     self.env['procurement.group'].run(procurements)
        return True

    def unlink(self):
        for order_line in self:
            items = order_line.order_id.sale_order_additional_ids.filtered(
                lambda l: l.line_id.id == order_line.id and l.is_button_clicked)
            for item in items:
                item.is_button_clicked = False
                break
            items = order_line.order_id.sale_order_option_ids.filtered(
                lambda l: l.line_id.id == order_line.id and l.is_button_clicked)
            for item in items:
                item.is_button_clicked = False
                break
        return super(SaleOrderLine, self).unlink()

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
            'tax_id': self.tax_id.id,
            'section': self.section.id,
            'company_id': self.order_id.company_id.id,
        }

    @api.depends('price_subtotal')
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

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            if not self.price_unit or self.price_unit == 0:
                self.price_unit = product._get_tax_included_unit_price(
                    self.company_id or self.order_id.company_id,
                    self.order_id.currency_id,
                    self.order_id.date_order,
                    'sale',
                    fiscal_position=self.order_id.fiscal_position_id,
                    product_price_unit=self._get_display_price(product),
                    product_currency=self.order_id.currency_id
                )
