
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_expense_module = fields.Boolean(string='Expense Module')
