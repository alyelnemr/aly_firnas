# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import timedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def get_analytic_tags(self):
        for line in self:
            line.analytic_tag_ids = line.order_id.analytic_tag_ids.ids

    def _prepare_invoice_line(self):
        res = super(InheritSaleLines, self)._prepare_invoice_line()
        res['analytic_account_id'] = self.order_id.analytic_account_id.id
        res['analytic_tag_ids'] = self.order_id.analytic_tag_ids.ids
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