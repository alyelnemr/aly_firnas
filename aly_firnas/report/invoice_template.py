# Copyright 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

import pytz
from odoo import api, fields, models, _


class PurchaseReportTemplatePrimary(models.AbstractModel):
    _name = 'report.aly_firnas.aly_invoice_template'
    _description = 'Invoice Report'

    def get_date_by_timezone(self, par_date):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        return pytz.utc.localize(par_date).astimezone(local).date()

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'account.move'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].sudo().browse(docids)
        line_section = docs.invoice_line_ids[0]
        amount_untaxed = sum(ol.price_subtotal for ol in docs.invoice_line_ids.filtered_domain([('is_printed', '=', True)]))

        amount_tax = 0
        discount = 0
        for line in docs.invoice_line_ids.filtered_domain([('is_printed', '=', True)]):
            discount += line.discount
            amount_tax += line.amount_tax
        is_discounted = discount > 0
        is_taxed = amount_tax > 0
        amount_total = (amount_untaxed + amount_tax)
        rep_vendor_name = docs.partner_id.name if docs.partner_id else ''
        rep_payment_term = docs.invoice_payment_term_id.name if docs.invoice_payment_term_id else ''
        rep_partner_ref = docs.ref if docs.ref else ''
        invoice_date = docs.invoice_date if docs.invoice_date else docs.date if docs.date else False
        payment_days = docs.invoice_payment_term_id.line_ids[0].days if docs.invoice_payment_term_id.line_ids else 0
        due_date = invoice_date + datetime.timedelta(days=payment_days)
        # docs.standard_payment_schedule = docs.standard_payment_schedule.replace('</p><p>', '<br />') if docs.standard_payment_schedule else False
        docs.terms_and_conditions = docs.terms_and_conditions.replace('</p><p>', '<br />') if docs.terms_and_conditions else False
        is_print_page_break = docs.terms_and_conditions
        is_print_payment_term = False #docs.is_print_payment_schedule
        is_print_terms_and_conditions = docs.is_print_terms_and_conditions
        col_span = 5
        if is_taxed or is_discounted:
            col_span = 6
        if is_taxed and is_discounted:
            col_span = 7
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'col_span': col_span,
            'is_discounted': is_discounted,
            'is_taxed': is_taxed,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'amount_untaxed': amount_untaxed,
            'amount_tax': amount_tax,
            'rep_vendor_name': rep_vendor_name,
            'rep_payment_term': rep_payment_term,
            'rep_partner_ref': rep_partner_ref,
            'is_print_payment_term': is_print_payment_term,
            'is_print_page_break': is_print_page_break,
            'is_print_terms_and_conditions': is_print_terms_and_conditions,
            'report_title': 'Invoice Report'
        }