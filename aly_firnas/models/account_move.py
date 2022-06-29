from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AcountMove(models.Model):
    _inherit = "account.move"

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

    amount_in_currency = fields.Monetary(string='Amount in Currency',
                                         currency_field='amount_currency_field', store=False, readonly=True,
                                         compute='_get_amount_from_currency')
    amount_currency_field = fields.Many2one('res.currency', 'Currency', required=False,
                                            readonly=True)
    amount_line_currency_field = fields.Many2one('res.currency', 'Currency', required=False,
                                            default=lambda self: self.company_id.currency_id.id, readonly=True)
    amount_line = fields.Monetary(string='Amount (Line)', store=False, readonly=True, compute='_get_amount_from_line',
                                  currency_field='amount_line_currency_field')

    manual_currency = fields.Boolean()
    is_manual = fields.Boolean(compute="_compute_currency")
    custom_rate = fields.Float(
        digits=(16, 10),
        tracking=True,
        help="Set new currency rate to apply on the invoice\n."
             "This rate will be taken in order to convert amounts between the "
             "current currency and last currency",
    )

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
        self.currency_id.rate = self.custom_rate

    def action_refresh_currency(self):
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Rate currency can refresh when state is draft only."))
        self._onchange_currency_change_rate(currency_changed=False)
        self.with_context(check_move_validity=False)._onchange_currency()
        return True
