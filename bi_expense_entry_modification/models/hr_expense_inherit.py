# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    # override expense credit account to take journal credit account
    def _get_expense_account_destination(self):
        self.ensure_one()
        result = super(HRExpense, self)._get_expense_account_destination()
        if self.sheet_id.journal_id.default_credit_account_id:
            result = self.sheet_id.journal_id.default_credit_account_id.id
        return result
