
from odoo import api, fields, models,_


class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    name = fields.Text('Description', required=False)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=False, domain="[('category_id', '=', product_uom_category_id)]")
    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    price_note = fields.Text("Price Note")
    is_present = fields.Boolean(string="Present on Quotation",
                                help="This field will be checked if the option line's product is "
                                     "already present in the quotation.",
                                compute="_compute_is_present", search="_search_is_present")
    is_button_clicked = fields.Boolean(default=False)
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    internal_notes = fields.Text(string='Internal Notes')
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Float(compute='_compute_amount', string='Total', readonly=True, store=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.quantity, product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_excluded'],
            })

    @api.depends('line_id', 'order_id.order_line', 'product_id')
    def _compute_is_present(self):
        # NOTE: this field cannot be stored as the line_id is usually removed
        # through cascade deletion, which means the compute would be false
        for option in self:
            # option.is_button_clicked = option.product_id.id in option.order_id.order_line.product_id.ids
            option.is_present = option.is_button_clicked

    def button_add_to_order(self):
        self.add_option_to_order()

    def add_option_to_order(self):
        self.ensure_one()

        sale_order = self.order_id
        values = self._get_values_to_add_to_order()
        order_line = self.env['sale.order.line'].create(values)

        self.write({'line_id': order_line.id, 'is_button_clicked': True})
        if sale_order:
            sale_order.add_option_to_order_with_taxcloud()

    def _get_values_to_add_to_order(self):
        self.ensure_one()
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'internal_notes': self.internal_notes,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': self.order_id.analytic_tag_ids.ids,
            'discount': self.discount,
            'tax_id': [(6, 0, self.tax_id.ids)],
            'company_id': self.order_id.company_id.id,
            'section': self.section.id
        }

    @api.onchange('product_id', 'uom_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.quantity,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.uom_id.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )
        self.name = product.get_product_multiline_description_sale()
        self.uom_id = self.uom_id or product.uom_id
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        # To compute the dicount a so line is created in cache
        values = self._get_values_to_add_to_order()
        new_sol = self.env['sale.order.line'].new(values)
        new_sol._onchange_discount()
        self.discount = new_sol.discount
        self.price_unit = new_sol._get_display_price(product)
        return {'domain': domain}

    def action_update_factor(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            custom_rate = self.order_id.custom_rate
            is_manual = self.order_id.is_manual
            if is_manual and custom_rate > 0:
                custom_rate = self.order_id.custom_rate
                line.price_unit *= custom_rate
