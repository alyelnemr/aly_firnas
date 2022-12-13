# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math
import base64


class InheritBankStatement(models.Model):
    _inherit = "account.bank.statement.line"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False)

    def _prepare_reconciliation_move(self, move_ref):
        """ Prepare the dict of values to create the move from a statement line. This method may be overridden to adapt domain logic
            through model inheritance (make sure to call super() to establish a clean extension chain).

           :param char move_ref: will be used as the reference of the generated account move
           :return: dict of value to create() the account.move
        """
        ref = move_ref or ''
        if self.ref:
            ref = move_ref + ' - ' + self.ref if move_ref else self.ref
        data = {
            'type': 'entry',
            'journal_id': self.statement_id.journal_id.id,
            'currency_id': self.statement_id.currency_id.id,
            'date': self.statement_id.accounting_date or self.date,
            'partner_id': self.partner_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': self.analytic_tag_ids,
            'ref': ref,
            'note': self.note,
        }
        if self.move_name:
            data.update(name=self.move_name)
        return data

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        payable_account_type = self.env.ref('account.data_account_type_payable')
        receivable_account_type = self.env.ref('account.data_account_type_receivable')
        suspense_moves_mode = self._context.get('suspense_moves_mode')
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env['account.move.line']
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env['account.move.line']

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        counterpart_moves = self.env['account.move']

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_('A selected move line was already reconciled.'))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled and not suspense_moves_mode:
                raise UserError(_('A selected move line was already reconciled.'))
            if isinstance(aml_dict['move_line'], int):
                aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])

        account_types = self.env['account.account.type']
        for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
            if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], int):
                # Transform the value in the format required for One2many and Many2many fields
                aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]

            user_type_id = self.env['account.account'].browse(aml_dict.get('account_id')).user_type_id
            if user_type_id in [payable_account_type, receivable_account_type] and user_type_id not in account_types:
                account_types |= user_type_id
        if suspense_moves_mode:
            if any(not line.journal_entry_ids for line in self):
                raise UserError(_('Some selected statement line were not already reconciled with an account move.'))
        else:
            if any(line.journal_entry_ids for line in self):
                raise UserError(_('A selected statement line was already reconciled with an account move.'))

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount
        currency = self.currency_id or statement_currency
        for aml_rec in payment_aml_rec:
            balance = aml_rec.amount_currency if aml_rec.currency_id else aml_rec.balance
            aml_currency = aml_rec.currency_id or aml_rec.company_currency_id
            total -= aml_currency._convert(balance, currency, aml_rec.company_id, aml_rec.date)
            aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
            counterpart_moves = (counterpart_moves | aml_rec.move_id)
            if aml_rec.journal_id.post_at == 'bank_rec' and aml_rec.payment_id and aml_rec.move_id.state == 'draft':
                # In case the journal is set to only post payments when performing bank
                # reconciliation, we modify its date and post it.
                aml_rec.move_id.date = self.date
                aml_rec.payment_id.payment_date = self.date
                aml_rec.move_id.post()
                # We check the paid status of the invoices reconciled with this payment
                for invoice in aml_rec.payment_id.reconciled_invoice_ids:
                    self._check_invoice_state(invoice)

        # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
        # case we reconcile the existing and the new move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            if suspense_moves_mode:
                self.button_cancel_reconciliation()
            move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
            if self.analytic_account_id and not move.analytic_account_id:
                move.analytic_account_id = self.analytic_account_id.id
            elif len(counterpart_aml_dicts) > 0 and counterpart_aml_dicts[0]['move_line'].analytic_account_id:
                if counterpart_aml_dicts[0]['move_line'].analytic_account_id and not move.analytic_account_id:
                    move.analytic_account_id = counterpart_aml_dicts[0]['move_line'].analytic_account_id.id
            elif len(new_aml_dicts) > 0 and new_aml_dicts[0].get('analytic_account_id'):
                if new_aml_dicts[0]['analytic_account_id'] and not move.analytic_account_id:
                    move.analytic_account_id = new_aml_dicts[0]['analytic_account_id']
            if self.analytic_tag_ids and not move.analytic_tag_ids:
                move.analytic_tag_ids = self.analytic_tag_ids
            elif len(counterpart_aml_dicts) > 0 and counterpart_aml_dicts[0]['move_line'].analytic_tag_ids:
                if counterpart_aml_dicts[0]['move_line'].analytic_tag_ids and not move.analytic_tag_ids:
                    move.analytic_tag_ids = counterpart_aml_dicts[0]['move_line'].analytic_tag_ids
            elif len(new_aml_dicts) > 0 and new_aml_dicts[0]['analytic_tag_ids']:
                if new_aml_dicts[0]['analytic_tag_ids'] and not move.analytic_tag_ids:
                    move.analytic_tag_ids = new_aml_dicts[0]['analytic_tag_ids']
            counterpart_moves = (counterpart_moves | move)

            # Create The payment
            payment = self.env['account.payment']
            partner_id = self.partner_id or (aml_dict.get('move_line') and aml_dict['move_line'].partner_id) or self.env[
                'res.partner']
            if abs(total) > 0.00001:
                payment_vals = self._prepare_payment_vals(total)
                if not payment_vals['partner_id']:
                    payment_vals['partner_id'] = partner_id.id
                if 'analytic_account_id' not in payment_vals:
                    if self.analytic_account_id:
                        payment_vals['analytic_account_id'] = self.analytic_account_id.id
                    elif move.analytic_account_id:
                        payment_vals['analytic_account_id'] = move.analytic_account_id.id
                    elif len(new_aml_dicts) > 0 and 'analytic_account_id' in new_aml_dicts[0]:
                        payment_vals['analytic_account_id'] = new_aml_dicts[0]['analytic_account_id']
                    elif len(counterpart_aml_dicts) > 0 and counterpart_aml_dicts[0]['move_line'].analytic_account_id:
                        if counterpart_aml_dicts[0]['move_line'].analytic_account_id:
                            payment_vals['analytic_account_id'] = counterpart_aml_dicts[0]['move_line'].analytic_account_id.id
                if 'analytic_tag_ids' not in payment_vals:
                    if self.analytic_tag_ids:
                        payment_vals['analytic_tag_ids'] = self.analytic_tag_ids
                    elif move.analytic_tag_ids:
                        payment_vals['analytic_tag_ids'] = move.analytic_tag_ids
                    elif len(new_aml_dicts) > 0 and 'analytic_tag_ids' in new_aml_dicts[0] and new_aml_dicts[0]['analytic_tag_ids']:
                        payment_vals['analytic_tag_ids'] = new_aml_dicts[0]['analytic_tag_ids']
                    elif len(counterpart_aml_dicts) > 0 and counterpart_aml_dicts[0]['move_line'].analytic_tag_ids:
                        if counterpart_aml_dicts[0]['move_line'].analytic_tag_ids:
                            payment_vals['analytic_tag_ids'] = counterpart_aml_dicts[0]['move_line'].analytic_tag_ids
                if payment_vals['partner_id'] and len(account_types) == 1:
                    payment_vals['partner_type'] = 'customer' if account_types == receivable_account_type else 'supplier'
                payment = payment.create(payment_vals)

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = (counterpart_aml_dicts + new_aml_dicts)
            date = self.date or fields.Date.today()
            for index, aml_dict in enumerate(to_create):
                analytic_account_id = self.analytic_account_id.id
                if not self.analytic_account_id:
                    if 'move_line' in aml_dict and aml_dict['move_line'].analytic_account_id:
                        analytic_account_id = aml_dict['move_line'].analytic_account_id.id
                    else:
                        analytic_account_id = aml_dict['analytic_account_id']
                analytic_tag_ids = self.analytic_tag_ids
                if not self.analytic_tag_ids:
                    if 'move_line' in aml_dict and aml_dict['move_line'].analytic_tag_ids:
                        analytic_tag_ids = aml_dict['move_line'].analytic_tag_ids
                    else:
                        analytic_tag_ids = aml_dict['analytic_tag_ids']
                aml_dict['move_id'] = move.id
                aml_dict['partner_id'] = self.partner_id.id
                aml_dict['statement_line_id'] = self.id
                aml_dict['analytic_tag_ids'] = analytic_tag_ids
                aml_dict['analytic_account_id'] = analytic_account_id
                self._prepare_move_line_for_currency(aml_dict, date)

            # Create write-offs
            for aml_dict in new_aml_dicts:
                aml_dict['payment_id'] = payment and payment.id or False
                aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if aml_dict['move_line'].payment_id and not aml_dict['move_line'].statement_line_id:
                    aml_dict['move_line'].write({'statement_line_id': self.id})
                if aml_dict['move_line'].partner_id.id:
                    aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
                aml_dict['account_id'] = aml_dict['move_line'].account_id.id
                aml_dict['payment_id'] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop('move_line')
                new_aml = aml_obj.with_context(check_move_validity=False, from_reconcile=True).create(aml_dict)

                (new_aml | counterpart_move_line).reconcile()

                self.with_context(from_reconcile=True)._check_invoice_state(counterpart_move_line.move_id)

            # Balance the move
            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict['payment_id'] = payment and payment.id or False
            aml_obj.with_context(check_move_validity=False, from_reconcile=True).create(aml_dict)

            move.with_context(from_reconcile=True).update_lines_tax_exigibility()  # Needs to be called manually as lines were created 1 by 1
            move.with_context(from_reconcile=True).post()
            # record the move name on the statement line to be able to retrieve it in case of unreconciliation
            self.write({'move_name': move.name})
            payment and payment.write({'payment_reference': move.name})
        elif self.move_name:
            raise UserError(
                _('Operation not allowed. Since your statement line already received a number (%s), you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.') % (
                    self.move_name))

        # create the res.partner.bank if needed
        if self.account_number and self.partner_id and not self.bank_account_id:
            # Search bank account without partner to handle the case the res.partner.bank already exists but is set
            # on a different partner.
            self.bank_account_id = self._find_or_create_bank_account()

        counterpart_moves._check_balanced()
        return counterpart_moves

