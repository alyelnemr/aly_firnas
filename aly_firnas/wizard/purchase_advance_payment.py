# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseAdvancePaymentInv(models.TransientModel):
    _name = "purchase.advance.payment.inv"
    _description = "Purchase Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _default_product_id(self):
        return self.env['product.product'].search([('type', '=', 'service'), ('is_downpayment_service', '=', True)], limit=1)

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_income_id

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.order_line.filtered(
                lambda purchase_order_line: purchase_order_line.is_downpayment
            )

        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.currency_id

    advance_payment_method = fields.Selection([
        ('delivered', 'Regular bill'),
        ('percentage', 'Milestone (percentage)'),
        ('fixed', 'Milestone (fixed amount)')
        ], string='Create Bill', default='delivered', required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing, \
        according to their invoicing policy (based on ordered or delivered quantity).")
    deduct_down_payments = fields.Boolean('Deduct down payments', default=True)
    has_down_payments = fields.Boolean('Has down payments', default=_default_has_down_payment, readonly=True)
    product_id = fields.Many2one('product.product', string=' Milestone Product', required=True,
                                 domain=[('type', '=', 'service'), ('is_downpayment_service', '=', True)],
                                 default =_default_product_id)
    downpayment_description = fields.Char(string='Description')
    count = fields.Integer(default=_count, string='Order Count')
    amount = fields.Float('Milestone Amount', digits='Account', help="The percentage of amount to be invoiced in advance, taxes excluded.")
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency_id)
    fixed_amount = fields.Monetary('Milestone (Fixed)', help="The fixed amount to be invoiced in advance, taxes excluded.")
    deposit_account_id = fields.Many2one("account.account", string="Income Account", domain=[('deprecated', '=', False)],
        help="Account used for deposits", default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="Taxes", help="Taxes used for deposits", default=_default_deposit_taxes_id)

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = self.default_get(['amount']).get('amount')
            return {'value': {'amount': amount}}
        return {}

    def _get_advance_details(self, order):
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            if all(self.product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = self.downpayment_description or _("Down payment of %s%%") % (self.amount)
        else:
            amount = self.fixed_amount
            name = self.downpayment_description or _('Down Payment')
        del context

        return amount, name

    def create_invoices(self):
        sale_orders = self.env['purchase.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.with_context(create_bill=True).action_create_invoice(final=self.deduct_down_payments)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['purchase.order.line']
            for order in sale_orders:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != 'order':
                    raise UserError(
                        _('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(
                        _("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
                else:
                    tax_ids = taxes.ids
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                so_line_values = self._prepare_purchase_line(order, analytic_tag_ids, tax_ids, amount, name)
                so_line = sale_line_obj.create(so_line_values)
                invoice = self._create_invoice(order, so_line, amount, self.deduct_down_payments)
                order.invoice_ids = [(4, invoice.id)]
        if self._context.get('open_invoices', False):
            return sale_orders.with_context(create_bill=False).action_return_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
            'company_id': False,
        }

    def _create_invoice(self, order, so_line, amount, final=False):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the down payment amount must be positive.'))

        amount, name = self._get_advance_details(order)
        invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)

        invoiceable_line_ids = []
        for line in order.order_line:
            if line.qty_to_invoice < 0 and final:# or line.is_downpayment:
                invoiceable_line_ids.append(line)
        for item in invoiceable_line_ids:
            if item.id != so_line.id:
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'name': item.name,
                    'purchase_line_id': item.id,
                    'price_unit': item.price_unit,
                    'quantity': 1.0 if not final else item.qty_to_invoice,
                    'discount': item.discount,
                    'product_id': item.product_id.id,
                    'product_uom_id': item.product_uom.id,
                    'tax_ids': [(6, 0, item.taxes_id.ids)],
                    'analytic_tag_ids': [(6, 0, item.analytic_tag_ids.ids)],
                    'analytic_account_id': item.account_analytic_id.id or False,
                }))

        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        invoice = self.env['account.move'].sudo().with_context(force_company=invoice_vals['company_id']).create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': order},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = {
            'ref': order.partner_ref,
            'type': 'in_invoice',
            'invoice_origin': order.name,
            'date': order.date_order,
            'invoice_date_due': order.date_order,
            'invoice_user_id': order.user_id.id,
            'invoice_payment_term_id': order.payment_term_id.id,
            'narration': order.name,
            'p_order_id': order.id,
            'purchase_id': order.id,
            'partner_id': order.partner_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'analytic_account_id': order.analytic_account_id.id,
            'analytic_tag_ids': order.analytic_tag_ids.ids,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'purchase_line_id': so_line.id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': so_line.discount,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.taxes_id.ids)],
                'purchase_downpayment_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': so_line.account_analytic_id.id or False,
            })],
        }

        return invoice_vals

    def _prepare_purchase_line(self, order, analytic_tag_ids, tax_ids, amount, name):
        context = {'lang': order.partner_id.lang}
        so_values = {
            'name': name or _('Down Payment: %s') % (time.strftime('%m %Y'),),
            'price_unit': amount,
            'product_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'date_planned': fields.Datetime.now(),
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'taxes_id': [(6, 0, tax_ids)],
            'account_analytic_id': order.analytic_account_id.id,
            'analytic_tag_ids': order.analytic_tag_ids.ids,
            'is_downpayment': True,
        }
        del context
        return so_values
