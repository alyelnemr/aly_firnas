from odoo import api, fields, models, _


class AlyResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    aly_po_scope_schedule = fields.Html(string="Scope and Schedule")
    aly_po_payment_schedule = fields.Html(string="Payment Schedule and Term")
    aly_po_acceptance = fields.Html(string="Acceptance")
    aly_complex_password = fields.Boolean(string='Activate Complex Password', default=True)
    date_sub_groups_ids = fields.Many2many(related='company_id.date_sub_groups_ids', string='Notification Groups',
                                           readonly=False)
    aly_expense_bank_journal_id = fields.Many2one('account.journal', string='Default Bank Journal',
                                                  domain="[('type', 'in', ['cash', 'bank'])]", check_company=False)

    def get_values(self):
        aly_res = super(AlyResConfigSettings, self).get_values()
        aly_res.update(
            aly_po_scope_schedule=self.env['ir.config_parameter'].sudo().get_param('aly_po_scope_schedule'),
            aly_po_payment_schedule=self.env['ir.config_parameter'].sudo().get_param('aly_po_payment_schedule'),
            aly_po_acceptance=self.env['ir.config_parameter'].sudo().get_param('aly_po_acceptance'),
            aly_complex_password=self.env['ir.config_parameter'].sudo().get_param('aly_complex_password'),
        )
        return aly_res

    def set_values(self):
        super(AlyResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('aly_po_scope_schedule', self.aly_po_scope_schedule)
        self.env['ir.config_parameter'].set_param('aly_po_payment_schedule', self.aly_po_payment_schedule)
        self.env['ir.config_parameter'].set_param('aly_po_acceptance', self.aly_po_acceptance)
        self.env['ir.config_parameter'].set_param('aly_complex_password', self.aly_complex_password)
