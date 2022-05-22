# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=False)

    def _prepare_payment_moves(self):
        res = super(InheritAccountPayment, self)._prepare_payment_moves()
        for move_vals in res:
            for line in move_vals['line_ids']:
                line[2]['analytic_account_id'] = self.analytic_account_id.id
                line[2]['analytic_tag_ids'] = self.analytic_tag_ids.ids
        # for payment, move_vals in zip(self, res):
        #     for line in move_vals['line_ids']:
        #         line[2]['analytic_account_id'] = payment.analytic_account_id.id
        #         line[2]['analytic_tag_ids'] = payment.analytic_tag_ids.ids
        return res
