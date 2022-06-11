from odoo import api, fields, models, _


class AlyResConfigSaleSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aly_so_payment_schedule = fields.Html(string="Payment Schedule")
    aly_so_terms_condition = fields.Html(string="Terms and Condition")

    def get_values(self):
        aly_res = super(AlyResConfigSaleSettings, self).get_values()
        aly_res.update(
            aly_so_payment_schedule=self.env['ir.config_parameter'].sudo().get_param('aly_so_payment_schedule'),
            aly_so_terms_condition=self.env['ir.config_parameter'].sudo().get_param('aly_so_terms_condition'),
        )
        return aly_res

    def set_values(self):
        super(AlyResConfigSaleSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('aly_so_payment_schedule', self.aly_so_payment_schedule)
        self.env['ir.config_parameter'].set_param('aly_so_terms_condition', self.aly_so_terms_condition)
