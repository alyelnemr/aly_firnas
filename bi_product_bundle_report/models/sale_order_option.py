from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    name = fields.Text('Description', required=False)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=False, domain="[('category_id', '=', product_uom_category_id)]")
    is_printed = fields.Boolean(string="Print?", default=True)
    section = fields.Many2one('sale.order.line.section', string="Section", required=True)
    price_note = fields.Char("Price Note")
    is_present = fields.Boolean(string="Present on Quotation",
                                help="This field will be checked if the option line's product is "
                                     "already present in the quotation.", default=False)
    is_button_clicked = fields.Boolean(default=False)

    @api.depends('line_id', 'order_id.order_line', 'product_id')
    def _compute_is_present(self):
        # NOTE: this field cannot be stored as the line_id is usually removed
        # through cascade deletion, which means the compute would be false
        for option in self:
            option.is_present = option.is_button_clicked

    def button_add_to_order(self):
        self.add_option_to_order()

    def add_option_to_order(self):
        self.ensure_one()

        sale_order = self.order_id
        self.write({'is_button_clicked': True})

        # if sale_order.state not in ['draft', 'sent', 'post']:
        #     raise UserError(_('You cannot add options to a confirmed order.'))

        values = self._get_values_to_add_to_order()
        order_line = self.env['sale.order.line'].create(values)
        order_line._compute_tax_id()

        self.write({'line_id': order_line.id})
        if sale_order:
            sale_order.add_option_to_order_with_taxcloud()

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
