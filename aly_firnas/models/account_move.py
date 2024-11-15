from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        for move in res:
            for line in move.line_ids:
                if line.tax_line_id:
                    line.analytic_account_id = move.analytic_account_id.id
                if line.tax_line_id:
                    line.analytic_tag_ids = move.analytic_tag_ids.ids
                if line.account_id and line.account_id.internal_type in ('payable', 'receivable'):
                    if self._context.get('from_reconcile', False):
                        line.analytic_account_id = move.analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id.id
                    else:
                        line.analytic_account_id = move.analytic_account_id.id
                if line.account_id and line.account_id.internal_type in ('payable', 'receivable'):
                    if self._context.get('from_reconcile', False):
                        line.analytic_tag_ids = move.analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids.ids
                    else:
                        line.analytic_tag_ids = move.analytic_tag_ids.ids
        return res

    def write(self, vals):
        lines = super(AccountMove, self).write(vals)
        for move in self:
            for line in move.line_ids:
                if ('analytic_account_id' in vals or 'analytic_tag_ids' in vals) and (not line.analytic_account_id or not line.analytic_tag_ids):
                    if line.account_id.internal_type in ('payable', 'receivable'):
                        if self._context.get('from_reconcile', False):
                            line.analytic_account_id = move.analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id.id
                            line.analytic_tag_ids = move.analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids.ids
                        else:
                            line.analytic_account_id = move.analytic_account_id.id
                            line.analytic_tag_ids = move.analytic_tag_ids.ids
                    else:
                        line.analytic_account_id = move.invoice_line_ids[0].analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id.id
                        line.analytic_tag_ids = move.invoice_line_ids[0].analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids.ids
        return lines

    @api.depends('line_ids.analytic_account_id', 'line_ids.analytic_tag_ids', 'invoice_line_ids.analytic_account_id',
                 'invoice_line_ids.analytic_tag_ids')
    def _compute_analytic_account_tag(self):
        for record in self:
            if record.line_ids:
                if record.line_ids[0].analytic_account_id:
                    record.analytic_account_id = record.line_ids[0].analytic_account_id.id
                else:
                    record.analytic_account_id = False

                if record.line_ids[0].analytic_tag_ids:
                    record.analytic_tag_ids = record.line_ids[0].analytic_tag_ids.ids
                else:
                    record.analytic_tag_ids = False
            else:
                record.analytic_account_id = False
                record.analytic_tag_ids = False

    def action_invoice_register_payment(self):
        res = super(AccountMove, self).action_invoice_register_payment()
        new_context = res['context'].copy()
        new_context['default_analytic_account_id'] = self.invoice_line_ids[0].analytic_account_id.id
        new_context['default_analytic_tag_ids'] = self.invoice_line_ids[0].analytic_tag_ids.ids
        res['context'] = new_context
        return res

    def _get_amount_from_line(self):
        for move in self:
            total = 0
            for line in move.line_ids:
                if line.debit >= 0:
                    total += line.debit
                move.amount_line_currency_field = line.company_currency_id.id

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_line = sign * total

    def _get_purchase_order_id(self):
        for line in self:
            line.purchase_order_id = line.p_order_id if line.p_order_id else False
            purchase_lines = self.env['purchase.order.line'].search([('invoice_lines.move_id.id', '=', line.id)])
            if purchase_lines:
                line.purchase_order_id = purchase_lines[0].order_id.id

    def _get_sale_order_id(self):
        for line in self:
            line.sale_order_id = line.s_order_id if line.s_order_id else False
            sale_lines = self.env['sale.order.line'].search([('invoice_lines.move_id.id', '=', line.id)])
            if sale_lines:
                line.sale_order_id = sale_lines[0].order_id.id

    def _get_amount_from_currency(self):
        for move in self:
            total = 0
            count = 0
            for line in move.line_ids:
                if line.amount_currency:
                    total += abs(line.amount_currency)
                    count += 1
                if line.amount_currency:
                    move.amount_currency_field = line.currency_id.id

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_in_currency = total / count if count > 0 else 0

    purchase_order_id = fields.Many2one('purchase.order', store=False,
                                  compute='_get_purchase_order_id',
                                  string='Purchase Order',)
    sale_order_id = fields.Many2one('sale.order', string="Sales Order", store=False,
                                    compute='_get_sale_order_id')
    p_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    s_order_id = fields.Many2one('sale.order', string="Sales Order")
    amount_in_currency = fields.Monetary(string='Amount in Currency',
                                         currency_field='amount_currency_field', store=False, readonly=True,
                                         compute='_get_amount_from_currency')
    amount_currency_field = fields.Many2one('res.currency', 'Currency', required=False,
                                            readonly=True)
    amount_line_currency_field = fields.Many2one('res.currency', 'Currency', required=False,
                                            default=lambda self: self.company_id.currency_id.id, readonly=True)
    amount_line = fields.Monetary(string='Amount (Line)', store=False, readonly=True, compute='_get_amount_from_line',
                                  currency_field='amount_line_currency_field')
    note = fields.Text(string='Notes')

    manual_currency = fields.Boolean()
    is_manual = fields.Boolean(compute="_compute_currency")
    custom_rate = fields.Float(
        digits=(16, 10),
        tracking=True, compute='_compute_currency_conversely', store=False,
        help="Set new currency rate to apply on the invoice\n."
             "This rate will be taken in order to convert amounts between the "
             "current currency and last currency",
    )
    custom_rate_conversely = fields.Float(
        digits=(16, 10),
        tracking=True,
        help="Set new currency rate to apply on the invoice\n."
             "This rate will be taken in order to convert amounts between the "
             "current currency and last currency",
    )

    @api.depends("currency_id", 'custom_rate', 'is_manual')
    def _compute_currency_conversely(self):
        for rec in self:
            rec.custom_rate = 1 / rec.custom_rate_conversely if rec.custom_rate_conversely > 0 else 0

    @api.depends("currency_id")
    def _compute_currency(self):
        for rec in self:
            rec.is_manual = rec.currency_id != rec.company_id.currency_id

    @api.onchange("currency_id", "date_order")
    def _onchange_currency_change_rate(self, currency_changed=True):
        today = self.date or self.invoice_date or fields.Date.today()
        main_currency = self.env.company.currency_id
        ctx = {"company_id": self.company_id.id, "date": today}
        custom_rate = main_currency.with_context(**ctx)._get_conversion_rate(
            main_currency, self.currency_id, self.company_id, today
        )
        if self.custom_rate != custom_rate and self.custom_rate > 0 and not currency_changed:
            currency_rate = self.env["res.currency.rate"]

            rate = self.custom_rate

            record = currency_rate.search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("currency_id", "=", self.currency_id.id),
                    ("name", "=", today),
                ],
                limit=1,
            )
            if record:
                record.write({"rate": rate})
            else:
                record = currency_rate.create(
                    {
                        "company_id": self.company_id.id,
                        "currency_id": self.currency_id.id,
                        "name": today,
                        "rate": rate,
                    }
                )
        else:
            self.custom_rate = custom_rate
            self.custom_rate_conversely = 1 / custom_rate if custom_rate > 0 else 0
        self.currency_id.rate = self.custom_rate

    def action_refresh_currency(self):
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Rate currency can refresh when state is draft only."))
        self._onchange_currency_change_rate(currency_changed=False)
        self.with_context(check_move_validity=False)._onchange_currency()
        return True

    def action_view_purchase_order(self):
        return {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('purchase.purchase_order_form').id,
            'target': 'self'
        }

    def action_view_sale_order(self):
        return {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'target': 'self'
        }
