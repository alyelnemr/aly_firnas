from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class SaleOrderAdditional(models.Model):
    _name = "sale.order.additional"
    _description = "Sale Alternative"
    _order = 'sequence, id'

    is_present = fields.Boolean(string="Present on Quotation",
                                help="This field will be checked if the option line's product is "
                                     "already present in the quotation.",
                                compute="_compute_is_present", search="_search_is_present")
    order_id = fields.Many2one('sale.order', 'Sales Order Reference', ondelete='cascade', index=True)
    line_id = fields.Many2one('sale.order.line', ondelete="set null", copy=False)
    name = fields.Text('Description', required=False)
    product_id = fields.Many2one('product.product', 'Product', required=True, domain=[('sale_ok', '=', True)])
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price')
    discount = fields.Float('Discount (%)', digits='Discount')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=False, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    quantity = fields.Float('Quantity', required=True, digits='Product UoS', default=1)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of optional products.")
    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    price_note = fields.Char("Price Note")
    is_button_clicked = fields.Boolean(default=False)
    internal_notes = fields.Text(string='Internal Notes')

    @api.depends('line_id', 'order_id.order_line', 'product_id')
    def _compute_is_present(self):
        # NOTE: this field cannot be stored as the line_id is usually removed
        # through cascade deletion, which means the compute would be false
        for option in self:
            option.is_button_clicked = option.product_id.id in option.order_id.order_line.product_id.ids
            option.is_present = option.is_button_clicked

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.name = record.product_id.description_sale
                if record.product_id.uom_id:
                    record.uom_id = record.product_id.uom_id.id
                else:
                    record.uom_id = False
            else:
                record.name = ''

    @api.onchange('product_id', 'uom_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id.with_context(lang=self.order_id.partner_id.lang)
        if not self.price_unit or self.price_unit == 0:
            self.price_unit = product.list_price
        self.name = self.get_sale_order_line_multiline_description_sale(product)
        self.uom_id = self.uom_id or product.uom_id
        pricelist = self.order_id.pricelist_id
        if pricelist and product:
            partner_id = self.order_id.partner_id.id
            self.price_unit = pricelist.with_context(uom=self.uom_id.id).get_product_price(product, self.quantity, partner_id)
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

    def button_add_to_order(self):
        self.add_additional_to_order()

    def add_additional_to_order(self):
        self.ensure_one()

        sale_order = self.order_id
        self.write({'is_button_clicked': True})

        # if sale_order.state not in ['draft', 'sent']:
        #     raise UserError(_('You cannot add additional to a confirmed order.'))

        values = self._get_values_to_add_to_order()
        order_line = self.env['sale.order.line'].create(values)
        order_line._compute_tax_id()

        self.write({'line_id': order_line.id})

    def _get_values_to_add_to_order(self):
        self.ensure_one()
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': self.order_id.analytic_tag_ids.ids,
            'discount': self.discount,
            'company_id': self.order_id.company_id.id,
            'section':self.section.id
        }

    def action_update_factor(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            custom_rate = self.order_id.custom_rate
            is_manual = self.order_id.is_manual
            if is_manual and custom_rate > 0:
                custom_rate = self.order_id.custom_rate
                line.price_unit *= custom_rate

    def get_sale_order_line_multiline_description_sale(self, product):
        return product.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()

    def _get_sale_order_line_multiline_description_variants(self):
        if not self.product_custom_attribute_value_ids and not self.product_no_variant_attribute_value_ids:
            return ""

        name = "\n"

        custom_ptavs = self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
        no_variant_ptavs = self.product_no_variant_attribute_value_ids._origin

        # display the no_variant attributes, except those that are also
        # displayed by a custom (avoid duplicate description)
        for ptav in (no_variant_ptavs - custom_ptavs):
            name += "\n" + ptav.with_context(lang=self.order_id.partner_id.lang).display_name

        # Sort the values according to _order settings, because it doesn't work for virtual records in onchange
        custom_values = sorted(self.product_custom_attribute_value_ids,
                               key=lambda r: (r.custom_product_template_attribute_value_id.id, r.id))
        # display the is_custom values
        for pacv in custom_values:
            name += "\n" + pacv.with_context(lang=self.order_id.partner_id.lang).display_name

        return name
