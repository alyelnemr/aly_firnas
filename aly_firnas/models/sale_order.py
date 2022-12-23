
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    , copy=False)
    is_manual = fields.Boolean('Manual Rate', default=False, readonly=False)
    custom_rate = fields.Float('Rate (Factor)', digits=(16, 12), tracking=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        readonly=True, copy=False, check_company=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True, copy=False)
    purchase_order_count = fields.Integer("Number of Purchase Order", compute='_compute_purchase_order_count',
                                          groups='purchase.group_purchase_user')

    @api.onchange('analytic_account_id', 'analytic_tag_ids')
    def update_analytic_tags(self):
        for line in self.order_line:
            line.analytic_account_id = self.analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id
            line.analytic_tag_ids = self.analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids

    @api.depends('order_line.purchase_line_ids')
    def _compute_purchase_order_count(self):
        purchase_line_data = self.env['purchase.order.line'].sudo().read_group(
            [('sale_order_id', 'in', self.ids)],
            ['sale_order_id', 'purchase_order_count:count_distinct(order_id)'], ['sale_order_id']
        )
        purchase_count_map = {item['sale_order_id'][0]: item['purchase_order_count'] for item in purchase_line_data}
        for order in self:
            order.purchase_order_count = purchase_count_map.get(order.id, 0)

    def action_confirm(self):
        for line in self:
            if not line.analytic_tag_ids or not line.analytic_account_id:
                raise ValidationError(_('You cannot Confirm until adding Analytic Tags and Analytic Accounts.'))
        res = super(SaleOrder, self).action_confirm()
        return res

    def _compute_option_data_for_template_change(self, option):
        if self.pricelist_id:
            price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1, False)
        else:
            price = option.price_unit
        return {
            'product_id': option.product_id.id,
            'name': option.name,
            'quantity': option.quantity,
            'uom_id': option.uom_id.id,
            'section': option.section,
            'price_unit': price,
            'tax_id': option.tax_ids,
            'discount': option.discount,
        }

    def _compute_line_data_for_template_change(self, line):
        vals = super(SaleOrder, self)._compute_line_data_for_template_change(line)
        vals.update(section=line.section)
        vals.update(tax_id=line.tax_ids)
        return vals

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            if line.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = line.price_unit
                else:
                    price = line.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - line.discount) / 100),
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                })
                # if self.pricelist_id:
                #     data.update(
                #         self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id, line.product_uom_id,
                #                                                         fields.Date.context_today(self)))
            order_lines.append((0, 0, data))
        self.order_line = order_lines
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            if option.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1,
                                                                                                   False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = option.price_unit
                else:
                    price = option.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - option.discount) / 100),
                })
            option_lines.append((0, 0, data))
        self.sale_order_option_ids = option_lines

        additional_lines = [(5, 0, 0)]
        for option in template.sale_order_template_additional_ids:
            data = self._compute_option_data_for_template_change(option)
            if option.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1,
                                                                                                           False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = option.price_unit
                else:
                    price = option.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - option.discount) / 100),
                })
            additional_lines.append((0, 0, data))
        self.sale_order_additional_ids = additional_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment
        if template.note:
            self.note = template.note
        for line in self.order_line:
            line.analytic_account_id = self.analytic_account_id.id
            line.analytic_tag_ids = self.analytic_tag_ids.ids

    def action_update_factor(self):
        for rec in self:
            for line in rec.order_line:
                line.action_update_factor()
            for line in rec.sale_order_option_ids:
                line.action_update_factor()
            for line in rec.sale_order_additional_ids:
                line.action_update_factor()

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['analytic_account_id'] = self.analytic_account_id.id
        invoice_vals['analytic_tag_ids'] = self.analytic_tag_ids.ids
        invoice_vals['s_order_id'] = self.id
        return invoice_vals
