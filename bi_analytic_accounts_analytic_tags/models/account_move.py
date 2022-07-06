# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.model
    def create(self, vals):
        res = super(InheritAccountMove, self).create(vals)
        for move in res:
            for item in move.line_ids:
                if item.account_id and item.account_id.internal_type == 'payable':
                    item.analytic_account_id = move.analytic_account_id
                    item.analytic_tag_ids = move.analytic_tag_ids
        return res

    def write(self, vals):
        lines = super(InheritAccountMove, self).write(vals)
        for move in self:
            for item in move.line_ids:
                if item.account_id.internal_type == 'payable':
                    item.analytic_account_id = move.analytic_account_id if not item.analytic_account_id else item.analytic_account_id
                    item.analytic_tag_ids = move.analytic_tag_ids if not item.analytic_tag_ids else item.analytic_tag_ids
                else:
                    item.analytic_account_id = move.invoice_line_ids[0].analytic_account_id if not item.analytic_account_id else item.analytic_account_id
                    item.analytic_tag_ids = move.invoice_line_ids[0].analytic_tag_ids if not item.analytic_tag_ids else item.analytic_tag_ids
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
        res = super(InheritAccountMove, self).action_invoice_register_payment()
        new_context = res['context'].copy()
        new_context['default_analytic_account_id'] = self.invoice_line_ids[0].analytic_account_id.id
        new_context['default_analytic_tag_ids'] = self.invoice_line_ids[0].analytic_tag_ids.ids
        res['context'] = new_context
        return res
