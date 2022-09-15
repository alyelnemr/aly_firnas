# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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
    custom_rate = fields.Float('Rate (Factor)', digits=(16, 12))
    #
    # @api.depends('pricelist_id', 'date_order', 'company_id')
    # def _compute_currency_rate(self):
    #     for order in self:
    #         if order.manual_currency_rate_active:
    #             order.currency_rate = self.env['res.currency'].with_context(override_currency_rate=self.manual_currency_rate)._get_conversion_rate(order.company_id.currency_id, order.currency_id, order.company_id, order.date_order)
    #             for item in order.order_line:
    #                 item.price_unit = order.currency_id.with_context(
    #                     override_currency_rate=self.manual_currency_rate)._convert(
    #                     item.price_unit, self.new_currency_id,
    #                     self.company_id or self.env.company, self.date_order or fields.Date.today())
    #             order.currency_id = self.new_currency_id
    #         else:
    #             order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id,order.currency_id, order.company_id,order.date_order)

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
            'discount': option.discount,
        }

    def _compute_line_data_for_template_change(self, line):
        vals = super(SaleOrder, self)._compute_line_data_for_template_change(line)
        vals.update(section=line.section)
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
                    price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1,
                                                                                                         False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = line.price_unit

                    # if self.pricelist_id.discount_policy == 'without_discount' and line.price_unit:
                    #     discount = (line.price_unit - price) / line.price_unit * 100
                    #     # negative discounts (= surcharge) are included in the display price
                    #     if discount < 0:
                    #         discount = 0
                    #     else:
                    #         price = line.price_unit
                    # elif line.price_unit:
                    #     price = line.price_unit

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
        self.order_line._compute_tax_id()
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
