
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
import textile
from odoo.tools.misc import formatLang, get_lang
from functools import partial
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    , copy=False)
    is_manual = fields.Boolean('Manual Rate', default=False, readonly=False)
    custom_rate = fields.Float('Rate (Factor)', digits=(16, 12), tracking=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        readonly=True, copy=False, check_company=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True, copy=False
                                        , states={'sale': [('readonly', True)]})
    purchase_order_count = fields.Integer("Number of Purchase Order", compute='_compute_purchase_order_count',
                                          groups='purchase.group_purchase_user')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company
                                 , states={'sale': [('readonly', True)]})
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

    @api.onchange('analytic_account_id', 'analytic_tag_ids')
    def update_analytic_tags(self):
        for line in self.order_line:
            line.analytic_account_id = self.analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id
            line.analytic_tag_ids = self.analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids

    @api.depends('order_line.purchase_line_ids')
    def _compute_purchase_order_count(self):
        purchase_line_data = self.env['purchase.order.line'].sudo().read_group(
            [('sale_order_id', 'in', self.ids)],
            ['sale_order_id', 'purchase_order_count:count_distinct(order_id)'], ['sale_order_id']
        )
        purchase_count_map = {item['sale_order_id'][0]: item['purchase_order_count'] for item in purchase_line_data}
        for order in self:
            order.purchase_order_count = purchase_count_map.get(order.id, 0)

    def action_confirm(self):
        for line in self:
            if not line.analytic_tag_ids or not line.analytic_account_id:
                raise ValidationError(_('You cannot Confirm until adding Analytic Tags and Analytic Accounts.'))
        res = super(SaleOrder, self).action_confirm()
        return res

    def _compute_option_data_for_template_change(self, option):
        if self.pricelist_id:
            price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1, False)
        else:
            price = option.price_unit
        return {
            'product_id': option.product_id.id,
            'name': option.name,
            'quantity': option.quantity,
            'uom_id': option.uom_id.id,
            'section': option.section,
            'price_unit': price,
            'tax_id': option.tax_ids,
            'discount': option.discount,
        }

    def _compute_line_data_for_template_change(self, line):
        vals = super(SaleOrder, self)._compute_line_data_for_template_change(line)
        vals.update(section=line.section)
        vals.update(tax_id=line.tax_ids)
        return vals

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            # 'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            # 'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)],
                                   user_id=user_id)
        self.update(values)

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            if line.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = line.price_unit
                else:
                    price = line.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - line.discount) / 100),
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                })
                # if self.pricelist_id:
                #     data.update(
                #         self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id, line.product_uom_id,
                #                                                         fields.Date.context_today(self)))
            order_lines.append((0, 0, data))
        self.order_line = order_lines
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            if option.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1,
                                                                                                   False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = option.price_unit
                else:
                    price = option.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - option.discount) / 100),
                })
            option_lines.append((0, 0, data))
        self.sale_order_option_ids = option_lines

        additional_lines = [(5, 0, 0)]
        for option in template.sale_order_template_additional_ids:
            data = self._compute_option_data_for_template_change(option)
            if option.product_id:
                discount = 0
                if self.pricelist_id:
                    price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1,
                                                                                                           False)
                    # get price from price list only if no price list get from template line price
                    if not price:
                        price = option.price_unit
                else:
                    price = option.price_unit

                data.update({
                    'price_unit': price,
                    'discount': 100 - ((100 - discount) * (100 - option.discount) / 100),
                })
            additional_lines.append((0, 0, data))
        self.sale_order_additional_ids = additional_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment
        if template.note:
            self.note = template.note
        for line in self.order_line:
            line.analytic_account_id = self.analytic_account_id.id
            line.analytic_tag_ids = self.analytic_tag_ids.ids

    def action_update_factor(self):
        for rec in self:
            for line in rec.order_line:
                line.action_update_factor()
            for line in rec.sale_order_option_ids:
                line.action_update_factor()
            for line in rec.sale_order_additional_ids:
                line.action_update_factor()

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['analytic_account_id'] = self.analytic_account_id.id
        invoice_vals['analytic_tag_ids'] = self.analytic_tag_ids.ids
        invoice_vals['s_order_id'] = self.id
        invoice_vals['partner_invoice_id'] = self.partner_invoice_id.id
        invoice_vals['partner_contact'] = self.partner_contact.id
        invoice_vals['standard_payment_schedule'] = self.standard_payment_schedule
        invoice_vals['terms_and_conditions'] = self.terms_and_conditions
        return invoice_vals

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