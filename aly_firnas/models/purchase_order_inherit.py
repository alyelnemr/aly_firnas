from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_default_po_scope_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_scope_schedule')

    def _get_default_po_payment_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_payment_schedule')

    def _get_default_po_acceptance(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_acceptance')

    is_print_delivery_section = fields.Boolean(string='Delivery Section', default=False, required=False)
    is_print_firnas_signature = fields.Boolean(string='Firnas Shuman Signature', default=False, required=False)
    is_print_vendor_signature = fields.Boolean(string='Vendor Signature', default=False, required=False)
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=False, domain="[('parent_id', '=', partner_id)]")
    po_scope_schedule = fields.Html(string="Scope and Schedule", default=_get_default_po_scope_schedule)
    po_payment_schedule = fields.Html(string="Payment Schedule and Term", default=_get_default_po_payment_schedule)
    po_acceptance = fields.Html(string="Acceptance", default=_get_default_po_acceptance)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends("discount")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price_unit()})
        return vals

    def _get_line_numbers(self):
        if self.ids:
            first_line_rec = self.browse(self.ids[0])
            x = 1
            self.line_rank = len(first_line_rec.order_id.order_line)
            for line in first_line_rec.order_id.order_line:
                line.line_rank = x
                x += 1

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals["discount"] = self.discount
        return vals

    def _get_discounted_price_unit(self):
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    def _get_stock_move_price_unit(self):
        price_unit = False
        price = self._get_discounted_price_unit()
        if price != self.price_unit:
            # Only change value if it's different
            price_unit = self.price_unit
            self.price_unit = price
        price = super()._get_stock_move_price_unit()
        if price_unit:
            self.price_unit = price_unit
        return price

    line_rank = fields.Integer('Sn', compute='_get_line_numbers', store=False, default=1)
    discount = fields.Float(string="Discount (%)", digits="Discount")
