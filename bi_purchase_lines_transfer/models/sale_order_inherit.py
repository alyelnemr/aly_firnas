# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritSaleLines(models.Model):
    _inherit = 'sale.order.line'

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        res = super()._purchase_service_prepare_line_values(purchase_order=purchase_order, quantity=quantity)
        res.update({
            "origin": self.order_id.name,
        })
        return res
