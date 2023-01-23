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
        model = 'account.invoice'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].sudo().browse(docids)
        line_section = docs.order_line[0]
        for indx, line in enumerate(docs.order_line):
            if line.display_type == 'line_section':
                line_section = line.name
                line.price_subtotal = 0.0
                for sub_line in docs.order_line[indx + 1:]:
                    if sub_line.display_type == 'line_section' and line.name != sub_line.name:
                        break
                    else:
                        line.price_subtotal += sub_line.price_subtotal

        discount = 0
        for line in docs.order_line:
            discount += line.discount
        is_discounted = discount > 0
        is_taxed = docs.amount_tax > 0
        rep_vendor_name = docs.partner_id.name if docs.partner_id else ''
        rep_payment_term = docs.payment_term_id.name if docs.payment_term_id else ''
        rep_partner_ref = docs.partner_ref if docs.partner_ref else ''
        order_date = docs.invoice_date.date() if docs.invoice_date else False
        invoice_date = self.get_date_by_timezone(docs.invoice_date)
        payment_days = docs.payment_term_id.line_ids[0].days if docs.payment_term_id.line_ids else 0
        due_date = invoice_date + datetime.timedelta(days=payment_days)
        docs.standard_payment_schedule = docs.standard_payment_schedule.replace('</p><p>', '<br />') if docs.standard_payment_schedule else False
        docs.terms_and_conditions = docs.terms_and_conditions.replace('</p><p>', '<br />') if docs.terms_and_conditions else False
        is_print_page_break = docs.standard_payment_schedule or docs.terms_and_conditions
        is_print_payment_term = True if docs.standard_payment_schedule else False
        is_print_terms_and_conditions = True if docs.terms_and_conditions else False
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
            'rep_vendor_name': rep_vendor_name,
            'rep_payment_term': rep_payment_term,
            'rep_partner_ref': rep_partner_ref,
            'is_print_payment_term': is_print_payment_term,
            'is_print_page_break': is_print_page_break,
            'is_print_terms_and_conditions': is_print_terms_and_conditions,
            'report_title': 'Invoice Report'
        }