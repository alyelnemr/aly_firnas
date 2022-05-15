# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    # vendor_contact = fields.Many2one('res.partner', string='Vendor Contact', domain="[('type', '=', 'contact')]")
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=True, domain="[('parent_id', '=', partner_id)]")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_line_numbers(self):
        if self.ids:
            first_line_rec = self.browse(self.ids[0])
            x = 1
            self.line_rank = len(first_line_rec.order_id.order_line)
            for line in first_line_rec.order_id.order_line:
                line.line_rank = x
                x += 1

    line_rank = fields.Integer('Serial', compute='_get_line_numbers', store=False, default=1)
