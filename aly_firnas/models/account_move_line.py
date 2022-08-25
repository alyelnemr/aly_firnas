from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        for line in self:
            if 'statement_line_id' in vals and line.payment_id:
                # In case of an internal transfer, there are 2 liquidity move lines to match with a bank statement
                if any(_line.statement_id for _line in line.payment_id.move_line_ids.filtered(
                        lambda r: r.id != line.id and r.account_id.internal_type == 'liquidity')):
                    line.payment_id.state = 'reconciled'
                    break