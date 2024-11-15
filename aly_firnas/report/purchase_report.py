# Copyright 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    discount = fields.Float(
        string="Discount (%)", digits="Discount", group_operator="avg"
    )

    def _select(self):
        res = super()._select()
        # There are 3 matches
        res = res.replace("l.price_unit", self._get_discounted_price_unit_exp())
        res += ", l.discount AS discount"
        return res

    def _group_by(self):
        res = super()._group_by()
        res += ", l.discount"
        return res

    def _get_discounted_price_unit_exp(self):
        """Inheritable method for getting the SQL expression used for
        calculating the unit price with discount(s).

        :rtype: str
        :return: SQL expression for discounted unit price.
        """
        return "(1.0 - COALESCE(l.discount, 0.0) / 100.0) * l.price_unit"


class PurchaseReportTemplatePrimary(models.AbstractModel):
    _name = 'report.aly_firnas.aly_rfq_main_template'
    _description = 'description'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'purchase.order'
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
        order_date = docs.date_order.date() if docs.date_order else False
        receipt_date = docs.date_planned.date() if docs.date_planned else False
        docs.po_scope_schedule = docs.po_scope_schedule.replace('</p><p>', '<br />') if docs.po_scope_schedule else False
        docs.po_payment_schedule = docs.po_payment_schedule.replace('</p><p>', '<br />') if docs.po_payment_schedule else False
        docs.po_acceptance = docs.po_acceptance.replace('</p><p>', '<br />') if docs.po_acceptance else False
        is_print_page_break = docs.is_print_scope_schedule or docs.is_print_payment_schedule or docs.is_print_acceptance
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'is_discounted': is_discounted,
            'is_taxed': is_taxed,
            'order_date': order_date,
            'receipt_date': receipt_date,
            'rep_vendor_name': rep_vendor_name,
            'rep_payment_term': rep_payment_term,
            'rep_partner_ref': rep_partner_ref,
            'is_print_page_break': is_print_page_break,
            'report_title': 'Purchase Order'
        }


class PurchaseReportTemplatePrimary(models.AbstractModel):
    _name = 'report.aly_firnas.aly_po_main_template'
    _description = 'description'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'purchase.order'
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
        order_date = docs.date_order.date() if docs.date_order else False
        receipt_date = docs.date_planned.date() if docs.date_planned else False
        docs.po_scope_schedule = docs.po_scope_schedule.replace('</p><p>', '<br />') if docs.po_scope_schedule else False
        docs.po_payment_schedule = docs.po_payment_schedule.replace('</p><p>', '<br />') if docs.po_payment_schedule else False
        docs.po_acceptance = docs.po_acceptance.replace('</p><p>', '<br />') if docs.po_acceptance else False
        is_print_page_break = docs.is_print_scope_schedule or docs.is_print_payment_schedule or docs.is_print_acceptance
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
            'order_date': order_date,
            'receipt_date': receipt_date,
            'rep_vendor_name': rep_vendor_name,
            'rep_payment_term': rep_payment_term,
            'rep_partner_ref': rep_partner_ref,
            'is_print_page_break': is_print_page_break,
            'report_title': 'Purchase Order'
        }