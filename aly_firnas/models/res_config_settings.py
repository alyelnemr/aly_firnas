from odoo import api, fields, models, _


class AlyResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aly_po_scope_schedule = fields.Html(string="Scope and Schedule")
    aly_po_payment_schedule = fields.Html(string="Payment Schedule and Term")
    aly_po_acceptance = fields.Html(string="Acceptance")

    def get_values(self):
        aly_res = super(AlyResConfigSettings, self).get_values()
        aly_res.update(
            aly_po_scope_schedule=self.env['ir.config_parameter'].sudo().get_param('aly_po_scope_schedule'),
            aly_po_payment_schedule=self.env['ir.config_parameter'].sudo().get_param('aly_po_payment_schedule'),
            aly_po_acceptance=self.env['ir.config_parameter'].sudo().get_param('aly_po_acceptance'),
        )
        return aly_res

    def set_values(self):
        super(AlyResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('aly_po_scope_schedule', self.aly_po_scope_schedule)
        self.env['ir.config_parameter'].set_param('aly_po_payment_schedule', self.aly_po_payment_schedule)
        self.env['ir.config_parameter'].set_param('aly_po_acceptance', self.aly_po_acceptance)
