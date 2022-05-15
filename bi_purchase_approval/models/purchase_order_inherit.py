# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError

READONLY_STATES = {
    'to approve': [('readonly', True)],
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('waiting approval', 'Waiting Approval'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    purchase_order_approve_user_id = fields.Many2one('res.users', string='User To Approve', states=READONLY_STATES)

    def action_submit_to_approve(self):
        for rec in self:
            if not rec.purchase_order_approve_user_id:
                raise UserError(_('Please Set User To Approve'))
            rec.state = 'waiting approval'

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'waiting approval']:
                continue
            if (order.purchase_order_approve_user_id and order.purchase_order_approve_user_id == self.env.user):
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step' \
                            and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
            else:
                raise ValidationError('You Are Not Allowed To Confirm!')
        return True
