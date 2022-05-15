# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super()._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, values, po)
        res.update({
            "origin": values['group_id'].sale_id.name,
        })
        return res
