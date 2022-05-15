# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    reinvoiced = fields.Boolean('Re-Invoiced?')

    def action_reinvoice_customer(self):
        for rec in self:
            wizard = self.env.ref('bi_purchase_reinvoice_customer.reinvoice_customer_wizard_view').id
            return {
                'name': _("Re-Invoice Customer"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'reinvoice.customer.wizard',
                'views': [(wizard, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_purchase_line_id': rec.id}
            }


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    show_reinvoice_customer = fields.Boolean(string="Is Re-invoice Customer", compute='compute_reinvoice_customer')

    @api.depends('origin')
    def compute_reinvoice_customer(self):
        for rec in self:
            if rec.origin:
                rec.show_reinvoice_customer = False
            else:
                rec.show_reinvoice_customer = True
