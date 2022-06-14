from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    name = fields.Text('Description', required=False)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=False, domain="[('category_id', '=', product_uom_category_id)]")
    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    price_note = fields.Char("Price Note")

    def button_add_to_order(self):
        self.add_option_to_order()

    def _get_values_to_add_to_order(self):
        self.ensure_one()
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'discount': self.discount,
            'section': self.section.id,
            'company_id': self.order_id.company_id.id,
        }


class SaleOrderAdditional(models.Model):
    _name = "sale.order.additional"
    _description = "Sale Alternative"
    _order = 'sequence, id'

    is_present = fields.Boolean(string="Present on Quotation",
                           help="This field will be checked if the additional line's product is "
                                "already present in the quotation.",compute="_compute_is_present")
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


    @api.depends('line_id', 'order_id.order_line', 'product_id')
    def _compute_is_present(self):
        # NOTE: this field cannot be stored as the line_id is usually removed
        # through cascade deletion, which means the compute would be false
        for additional in self:
            additional.is_present = bool(additional.order_id.order_line.filtered(lambda l: l.product_id == additional.product_id))

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
        self.price_unit = product.list_price
        self.name = product.get_product_multiline_description_sale()
        self.uom_id = self.uom_id or product.uom_id
        pricelist = self.order_id.pricelist_id
        if pricelist and product:
            partner_id = self.order_id.partner_id.id
            self.price_unit = pricelist.with_context(uom=self.uom_id.id).get_product_price(product, self.quantity, partner_id)
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

    def button_add_to_order(self):
        self.add_option_to_order()

    def add_option_to_order(self):
        self.ensure_one()

        sale_order = self.order_id

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
            'discount': self.discount,
            'section': self.section.id,
            'company_id': self.order_id.company_id.id,
            'section':self.section.id
        }