from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_line_numbers(self):
        if self.ids:
            first_line_rec = self.browse(self.ids[0])
            x = 1
            line_ids = first_line_rec.move_id.line_ids if first_line_rec.move_id.type == 'entry' else first_line_rec.move_id.invoice_line_ids
            self.line_rank = len(line_ids)
            for line in line_ids:
                if not line.display_type:
                    line.line_rank = x
                    x += 1

    note = fields.Text(string='Notes', related='statement_line_id.note')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)
    is_origin_so = fields.Boolean(copy=False)
    is_printed = fields.Boolean(string="Print?", default=True)
    line_rank = fields.Integer('Sn', compute='_get_line_numbers', store=False, default=1)

    purchase_downpayment_line_ids = fields.Many2many(
        'purchase.order.line',
        'purchase_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Purchase Order Lines', readonly=True, copy=False)

    @api.onchange('product_id')
    def get_analytic_default(self):
        for rec in self:
            if not rec.analytic_account_id and rec.move_id.analytic_account_id:
                rec.analytic_account_id = rec.move_id.analytic_account_id.id
            if not rec.analytic_tag_ids and rec.move_id.analytic_tag_ids:
                rec.analytic_tag_ids = rec.move_id.analytic_tag_ids.ids

    @api.model_create_multi
    def create(self, vals):
        lines = super(AccountMoveLine, self).create(vals)
        for line in lines:
            if line.move_id:
                analytic_account_id = line.move_id.analytic_account_id.id
                analytic_tag_ids = line.move_id.analytic_tag_ids.ids
            if analytic_account_id and not line.analytic_account_id:
                line.analytic_account_id = analytic_account_id
            if analytic_tag_ids and not line.analytic_tag_ids:
                line.analytic_tag_ids = analytic_tag_ids
        return lines

    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        for line in self:
            if 'statement_line_id' in vals and line.payment_id:
                # In case of an internal transfer, there are 2 liquidity move lines to match with a bank statement
                if any(_line.statement_id for _line in line.payment_id.move_line_ids.filtered(
                        lambda r: r.id != line.id and r.account_id.internal_type == 'liquidity')):
                    line.payment_id.state = 'reconciled'
                    break
