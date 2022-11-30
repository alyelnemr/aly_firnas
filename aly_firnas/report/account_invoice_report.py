# -*- coding: utf-8 -*-

from odoo import models, fields, api
from functools import lru_cache


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    is_printed = fields.Boolean(string="Print?", default=True)

    @api.model
    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", line.is_printed"

    @api.model
    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", line.is_printed"

    @api.model
    def _where(self):
        return '''
            WHERE move.type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
                AND line.account_id IS NOT NULL
                AND NOT line.exclude_from_invoice_tab
                AND line.is_printed = 't'
        '''

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        @lru_cache(maxsize=32)  # cache to prevent a SQL query for each data point
        def get_rate(currency_id):
            return self.env['res.currency']._get_conversion_rate(
                self.env['res.currency'].browse(currency_id),
                self.env.company.currency_id,
                self.env.company,
                self._fields['invoice_date'].today()
            )

        # First we get the structure of the results. The results won't be correct in multi-currency,
        # but we need this result structure.
        # By adding 'ids:array_agg(id)' to the fields, we will be able to map the results of the
        # second step in the structure of the first step.
        result_ref = super(AccountInvoiceReport, self).read_group(
            domain, fields + ['ids:array_agg(id)'], groupby, offset, limit, orderby, lazy
        )

        # In mono-currency, the results are correct, so we don't need the second step.
        if len(self.env.companies.mapped('currency_id')) <= 1:
            return result_ref

        # Reset all fields needing recomputation.
        for res_ref in result_ref:
            for field in {'amount_total', 'price_average', 'price_subtotal', 'residual'} & set(res_ref):
                res_ref[field] = 0.0

        # Then we perform another read_group, but this time we group by 'currency_id'. This way, we
        # are able to convert in batch in the current company currency.
        # During the process, we fill in the result structure we got in the previous step. To make
        # the mapping, we use the aggregated ids.
        result = super(AccountInvoiceReport, self).read_group(
            domain, fields + ['ids:array_agg(id)'], set(groupby) | {'currency_id'}, offset, limit, orderby, lazy
        )
        for res in result:
            if res.get('currency_id') and self.env.company.currency_id.id != res['currency_id'][0]:
                for field in {'amount_total', 'price_average', 'price_subtotal', 'residual'} & set(res):
                    res[field] = self.env.company.currency_id.round((res[field] or 0.0) * get_rate(res['currency_id'][0]))
            # Since the size of result_ref should be resonable, it should be fine to loop inside a
            # loop.
            for res_ref in result_ref:
                if res.get('ids') and res_ref.get('ids') and set(res['ids']) <= set(res_ref['ids']):
                    for field in {'amount_total', 'price_subtotal', 'residual'} & set(res_ref):
                        res_ref[field] += res[field]
                    for field in {'price_average'} & set(res_ref):
                        res_ref[field] = (res_ref[field] + res[field]) / 2 if res_ref[field] else res[field]

        return result_ref

    @api.model
    def _get_report_values(self, docids, data=None):
        return


class ReportInvoiceWithPayment(models.AbstractModel):
    _inherit = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        var_taxed_amount = 0
        for item in docs.invoice_line_ids.filtered_domain([('is_printed', '=', True)]):
            for tax in item.tax_ids:
                var_taxed_amount += ((item.quantity * item.price_unit) * tax.amount / 100)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'var_taxed_amount': var_taxed_amount,
            'report_type': data.get('report_type') if data else '',
        }
