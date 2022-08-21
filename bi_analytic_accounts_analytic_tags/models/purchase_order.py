# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re


class InheritPurchase(models.Model):
    _inherit = 'purchase.order'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)
    is_origin_so = fields.Boolean(default=False, copy=False)

    @api.onchange('analytic_account_id')
    def update_analytic_account(self):
        for line in self.order_line:
            line.account_analytic_id = self.analytic_account_id.id

    @api.onchange('analytic_tag_ids')
    def update_analytic_tags(self):
        for line in self.order_line:
            line.analytic_tag_ids = self.analytic_tag_ids.ids


class InheritPurchaseLines(models.Model):
    _inherit = 'purchase.order.line'
    is_origin_so = fields.Boolean(default=False, copy=False)

    @api.onchange('product_id')
    def get_analytic_account_tags(self):
        for line in self:
            # if not line.sale_order_id:
            line.account_analytic_id = line.order_id.analytic_account_id.id
            line.analytic_tag_ids = line.order_id.analytic_tag_ids.ids

    def _prepare_account_move_line(self, move):
        res = super()._prepare_account_move_line(move)
        res.update({'analytic_account_id': self.order_id.analytic_account_id})
        res.update({'analytic_tag_ids': self.order_id.analytic_tag_ids})
        res.update({'is_origin_so': self.order_id.is_origin_so})
        return res
