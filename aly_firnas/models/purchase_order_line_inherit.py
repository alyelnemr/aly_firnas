from odoo import api, fields, models, _


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
    date_order = fields.Date(related='order_id.date_order', string='Order Date', readonly=False, default=fields.Datetime.now)
