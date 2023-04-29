from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    aly_expense_bank_journal_id = fields.Many2one('account.journal', string='Expenses - Default Bank Journal',
                                                  domain="[('company_id', '=', id), ('type', 'in', ['cash', 'bank'])]", check_company=True)
    date_sub_groups_ids = fields.Many2many('res.groups', string='Notification Groups')
