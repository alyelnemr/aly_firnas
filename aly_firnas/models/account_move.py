from odoo import api, fields, models, _


class AcountMove(models.Model):
    _inherit = "account.move"

    def _get_amount_from_line(self):
        for move in self:
            total = 0
            for line in move.line_ids:
                if line.debit >= 0:
                    total += line.debit

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_line = sign * total

    amount_line = fields.Monetary(string='Amount (Line)', store=False, readonly=True, compute='_get_amount_from_line')
