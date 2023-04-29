# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero
import textile
from odoo.tools.misc import formatLang, get_lang
from functools import partial
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_additional_ids = fields.One2many(
        'sale.order.additional', 'order_id', 'Additional Products Lines',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]})
    sale_order_option_ids = fields.One2many(
        'sale.order.option', 'order_id', 'Optional Products Lines',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]})
    show_component_price = fields.Boolean(string="Show Component Price", default=False)

    split_page = fields.Boolean(string='Split Page?')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if not self._context.get('ignore', False):
            raise UserError('You cannot duplicate record from this action!')
        return super(SaleOrder, self).copy(default)

    def action_view_opportunity(self):
        action = self.env.ref('crm.crm_lead_opportunities').read()[0]
        # operator = 'child_of' if self..is_company else '='
        action['domain'] = [('id', '=', self.opportunity_id.id), ('type', '=', 'opportunity')]
        action['view_mode'] = 'form'
        action['view_type'] = 'form'
        action['res_id'] = self.opportunity_id.id
        action['views'] = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
        return action

    def print_bundled_quotation(self):
        self.ensure_one()
        order_lines = self.order_line
        data = {}

        sections = order_lines.mapped('section')
        all_sections = []
        for line in order_lines:
            if line['section'] not in all_sections:
                all_sections.append(line['section'])
        for section in all_sections:
            order_lines_count = order_lines.filtered(
                lambda l: l.section.id == section.id and l.is_printed is True and not self.is_sub_product(l))
            if order_lines_count:
                data[str(section.id if section.id else 0)] = {
                    'name': section.name if section.name else '(undefined)',
                    'total_price': sum([
                        (ol.price_subtotal if not ol.product_id.child_line else ol.price_unit * ol.product_uom_qty) for ol in
                        order_lines.filtered(lambda l: l.section.id == section.id and l.is_printed is True)
                    ]),
                    'lines': [{
                        'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                                + ol.product_id.name,
                        'desc': textile.textile(ol.name) if ol.name else '',
                        'qty': int(ol.product_uom_qty),
                        'total_price': ol.price_subtotal,
                        'tax_id': ol.tax_id,
                        'item_price': ol.item_price,
                        # 'price_unit': ol.price_unit,
                        'price_unit': round(ol.item_price / (int(ol.product_uom_qty) * (1 - (ol.discount / 100))), 2) if (
                                    int(ol.product_uom_qty) * (1 - (ol.discount / 100))) > 0 else 0,
                        'discount': ol.discount,
                        'is_update': ol.is_update,
                        'sub_lines': ol.get_orderline_sublines()
                    } for ol
                        in order_lines.filtered(lambda l: l.section.id == section.id and l.is_printed is True and not self.is_sub_product(l))]

                }
                # and l.bundle_status in ('bundle','bundel_of_bundle')
        return data

    def is_sub_product(self,line, check_is_printed=False):
        if check_is_printed:
            return self.order_line.filtered(lambda l: l.id == line.parent_order_line.id and line.parent_order_line.is_printed)
        return self.order_line.filtered(lambda l: l.id == line.parent_order_line.id)

    def is_updated_bundle(self,line):
        return line.get_orderline_sublines()

    def get_optional_lines(self):
        self.ensure_one()
        order_lines = self.sale_order_option_ids
        data = {}

        sections = order_lines.mapped('section')
        all_sections = []
        for line in order_lines:
            if line['section'] not in all_sections:
                all_sections.append(line['section'])
        for section in all_sections:
            lines_count = order_lines.filtered(lambda l: l.section.id == section.id and not l.is_button_clicked)
            if lines_count:
                data[str(section.id if section.id else 0)] = {
                    'name': section.name if section.name else '(undefined)',
                    'lines': [
                        {
                            'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                                    + ol.product_id.name,
                            'desc': textile.textile(
                                ol.name) if ol.name else '',
                            'qty': int(ol.quantity),
                            'total_price': ol.quantity * (ol.price_unit - (ol.price_unit * ol.discount / 100)),
                            'price_note': ol.price_note,
                            'price_unit': ol.price_unit,
                            'discount': ol.discount,
                            'tax_id': ol.tax_id,
                            'disc': str(round(ol.discount)) + '%'
                        } for ol in
                        order_lines.filtered(lambda l: l.section.id == section.id and not l.is_button_clicked)
                    ]
                }
        return data

    def get_additional_lines(self):
        self.ensure_one()
        order_lines = self.sale_order_additional_ids
        data = {}

        sections = order_lines.mapped('section')
        all_sections = []
        for line in order_lines:
            if line['section'] not in all_sections:
                all_sections.append(line['section'])
        for section in all_sections:
            lines_count = order_lines.filtered(lambda l: l.section.id == section.id and not l.is_button_clicked)
            if lines_count:
                data[str(section.id if section.id else 0)] = {
                    'name': section.name if section.name else '(undefined)',
                    'lines': [
                        {
                            'name': ('[%s] ' % ol.product_id.default_code if ol.product_id.default_code else '')
                                    + ol.product_id.name,
                            'desc': textile.textile(
                                ol.name) if ol.name else '',
                            'qty': int(ol.quantity),
                            'total_price': ol.quantity * (ol.price_unit - (ol.price_unit * ol.discount / 100)),
                            'price_note': ol.price_note,
                            'price_unit': ol.price_unit,
                            'discount': ol.discount,
                            'tax_id': ol.tax_id,
                            'disc': str(round(ol.discount)) + '%'
                        } for ol in
                        order_lines.filtered(lambda l: l.section.id == section.id and not l.is_button_clicked)
                    ]
                }
        return data

    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            item_price = line.item_price if line.item_price > 0 else line.price_unit
            for line in order.order_line:
                total += (line.price_subtotal * 100) / (100 - line.discount) if line.discount != 100 else (
                        item_price * line.product_uom_qty)
            order.amount_undiscounted = total

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                item_price = line.item_price if line.item_price > 0 else line.price_unit
                price_reduce = item_price * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=order.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]