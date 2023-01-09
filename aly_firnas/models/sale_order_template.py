# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import timedelta


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    sale_order_template_additional_ids = fields.One2many('sale.order.template.additional',
                                                         'sale_order_template_id', 'Additional Products', copy=True)


class SaleOrderTemplateAdditional(models.Model):
    _name = "sale.order.template.additional"
    _description = "Quotation Template Additional Products"
    _check_company_auto = True

    sale_order_template_id = fields.Many2one('sale.order.template', 'Quotation Template Reference', ondelete='cascade',
                                             index=True, required=True)

    sequence = fields.Integer('Sequence', default=1)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    company_id = fields.Many2one('res.company', related='sale_order_template_id.company_id', store=True, index=True)
    name = fields.Text('Description', required=True, translate=True)
    product_id = fields.Many2one(
        'product.product', 'Product', domain=[('sale_ok', '=', True)],
        required=True, check_company=True)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price')
    discount = fields.Float('Discount (%)', digits='Discount')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True,
                             domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    quantity = fields.Float('Quantity', required=True, digits='Product UoS', default=1)
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id
        self.price_unit = product.lst_price
        name = product.name
        if self.product_id.description_sale:
            name += '\n' + self.product_id.description_sale
        self.name = name
        self.uom_id = product.uom_id
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

    @api.onchange('uom_id')
    def _onchange_product_uom(self):
        if not self.product_id:
            return
        if not self.uom_id:
            self.price_unit = 0.0
            return
        if self.uom_id.id != self.product_id.uom_id.id:
            self.price_unit = self.product_id.uom_id._compute_price(self.product_id.lst_price, self.uom_id)


class SaleOrderTemplateOption(models.Model):
    _inherit = "sale.order.template.option"

    sequence = fields.Integer('Sequence', default=1)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')

