# Copyright 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SalesOrderReport(models.AbstractModel):
    _name = 'report.bi_product_bundle_report.report_bundled_saleorder'
    _description = 'description'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'sale.order'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].sudo().browse(docids)
        is_additional_exists = any(docs.sale_order_additional_ids.filtered(lambda o: not o.is_button_clicked))
        is_optional_exists = any(docs.sale_order_option_ids.filtered(lambda o: not o.is_button_clicked))
        amount_untaxed = sum([
            (ol.price_subtotal if not ol.product_id.child_line else round(
                ol.item_price / (int(ol.product_uom_qty) * (1 - (ol.discount / 100))), 2)) for ol in
            docs.order_line.filtered(lambda l: l.is_printed and (not l.parent_order_line or l.parent_order_line.is_printed))
        ])

        amount_tax = 0
        discount = 0
        for line in docs.order_line.filtered(lambda l: l.is_printed and (
                not l.parent_order_line or l.parent_order_line.is_printed)):
            if not docs.order_line.filtered(lambda l: l.id == line.parent_order_line.id):
                discount += line.discount
                amount_tax += line.price_tax
            else:
                amount_tax += line.price_tax
        is_discounted = discount > 0
        is_taxed = amount_tax > 0
        is_taxed_optional = any(docs.sale_order_option_ids.filtered(lambda o: o.tax_id and not o.is_button_clicked))
        is_taxed_additional = any(docs.sale_order_additional_ids.filtered(lambda o: o.tax_id and not o.is_button_clicked))
        amount_total = (amount_untaxed + amount_tax)
        col_span = 4
        if is_taxed or is_discounted:
            col_span = 5
        if is_taxed and is_discounted:
            col_span = 6
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'col_span': col_span,
            'is_discounted': is_discounted,
            'is_taxed': is_taxed,
            'is_taxed_optional': is_taxed_optional,
            'is_taxed_additional': is_taxed_additional,
            'amount_untaxed': amount_untaxed,
            'amount_tax': amount_tax,
            'amount_total': amount_total,
            'is_additional_exists': is_additional_exists,
            'is_optional_exists': is_optional_exists,
            'report_title': 'Purchase Order'
        }