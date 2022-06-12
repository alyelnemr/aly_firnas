from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False)

    def _prepare_payment_moves(self):
        res = super(InheritAccountPayment, self)._prepare_payment_moves()
        for move_vals in res:
            for line in move_vals['line_ids']:
                if line[2]['debit'] <= 0:
                    line[2]['analytic_account_id'] = self.invoice_ids[0].analytic_account_id.id
                    line[2]['analytic_tag_ids'] = self.invoice_ids[0].analytic_tag_ids.ids
                else:
                    line[2]['analytic_account_id'] = self.analytic_account_id.id
                    line[2]['analytic_tag_ids'] = self.analytic_tag_ids.ids
        # for payment, move_vals in zip(self, res):
        #     for line in move_vals['line_ids']:
        #         line[2]['analytic_account_id'] = payment.analytic_account_id.id
        #         line[2]['analytic_tag_ids'] = payment.analytic_tag_ids.ids
        return res

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            for line in moves.line_ids:
                if line.debit <= 0:
                    line.analytic_account_id = rec.invoice_ids[0].analytic_account_id.id
                    line.analytic_tag_ids = rec.invoice_ids[0].analytic_tag_ids.ids
                else:
                    line.analytic_account_id = rec.analytic_account_id.id
                    line.analytic_tag_ids = rec.analytic_tag_ids.ids
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (
                                line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()

        return True