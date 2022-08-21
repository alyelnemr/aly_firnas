from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, get_lang
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


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
                if not line.display_type:
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

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
                self.price_unit = 0.0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id,
                                                                             self.taxes_id, self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        if not self.price_unit or self.price_unit <= 0:
            self.price_unit = price_unit
        product_ctx = {'seller_id': seller.id, 'lang': get_lang(self.env, self.partner_id.lang).code}
        # self.name = self._get_product_purchase_description(self.product_id.with_context(**product_ctx))