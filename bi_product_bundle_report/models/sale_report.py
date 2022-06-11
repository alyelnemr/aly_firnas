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
        discount = 0
        for line in docs.order_line:
            discount += line.discount
        is_discounted = discount > 0
        is_taxed = docs.amount_tax > 0
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
            'report_title': 'Purchase Order'
        }