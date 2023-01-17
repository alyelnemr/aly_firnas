from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    manual_currency = fields.Boolean()
    is_manual = fields.Boolean(compute="_compute_currency")
    custom_rate = fields.Float(
        digits=(16, 10),
        tracking=True,
        help="Set new currency rate to apply on the invoice\n."
             "This rate will be taken in order to convert amounts between the "
             "current currency and last currency",
    )

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False)

    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        for move_vals in res:
            for line in move_vals['line_ids']:
                line[2]['analytic_account_id'] = self.analytic_account_id.id
                line[2]['analytic_tag_ids'] = self.analytic_tag_ids.ids
        return res

    def check_reconciliation(self):
        # when making a reconciliation on an existing liquidity journal item, mark the payment as reconciled
        for payment in self:
            for line in payment.move_line_ids:
                # count of all lines, then remove 1 to count all without the same line of comparison
                main_counter = len(payment.move_line_ids) - 1
                counter = 0
                if line.payment_id:
                    for _line in line.payment_id.move_line_ids:
                        if _line.id != line.id and _line.account_id.internal_type == 'liquidity':
                            if _line.statement_id:
                                counter += 1
                if counter == main_counter:
                    line.payment_id.state = 'reconciled'
                    # # In case of an internal transfer, there are 2 liquidity move lines to match with a bank statement
                    # if any(_line.statement_id for _line in line.payment_id.move_line_ids.filtered(
                    #         lambda r: r.id != line.id and r.account_id.internal_type == 'liquidity')):
                    #     line.payment_id.state = 'reconciled'
                    #     break

    @api.depends("currency_id")
    def _compute_currency(self):
        for rec in self:
            rec.is_manual = rec.currency_id != rec.company_id.currency_id

    @api.onchange("currency_id", 'date_order')
    def _onchange_currency_change_rate(self, currency_changed=True):
        today = self.payment_date or fields.Date.today()
        main_currency = self.env.company.currency_id
        ctx = {"company_id": self.company_id, "date": today}
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
        x = self.currency_id.rate
        print(x)

    def action_refresh_currency(self):
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Rate currency can refresh when state is draft only."))
        self._onchange_currency_change_rate(currency_changed=False)
        return True
