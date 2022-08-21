# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class InheritSales(models.Model):
    _inherit = 'sale.order'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        readonly=True, copy=False, check_company=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False, copy=False)

    @api.onchange('analytic_tag_ids')
    def update_analytic_tags(self):
        for line in self.order_line:
            line.analytic_tag_ids = self.analytic_tag_ids.ids

    def action_confirm(self):
        for line in self:
            if not line.analytic_tag_ids or not line.analytic_account_id:
                raise ValidationError(_('You cannot Confirm until adding Analytic Tags and Analytic Accounts.'))
        res = super(InheritSales, self).action_confirm()
        return res


class InheritSaleLines(models.Model):
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
        purchase_order.analytic_account_id=self.order_id.analytic_account_id.id
        purchase_order.analytic_tag_ids=self.order_id.analytic_tag_ids.ids
        res.update({
            "account_analytic_id": self.order_id.analytic_account_id.id,
            "analytic_tag_ids": self.order_id.analytic_tag_ids.ids,
            "is_origin_so":True,
        })
        
        return res
