from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = ['res.config.settings']

    number_increment = fields.Integer(string="Step")
    number_next_actual = fields.Integer(string="Next Number")

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        seq_obj = self.env['ir.sequence'].sudo().search([('code', '=', 'bi_crm_concatenated_name.serial_no')])
        res['number_increment'] = seq_obj.number_increment
        res['number_next_actual'] = seq_obj.number_next_actual
        return res

    @api.model
    def set_values(self):
        seq_obj = self.env['ir.sequence'].sudo().search([('code', '=', 'bi_crm_concatenated_name.serial_no')])
        seq_obj.write({
            'number_increment': self.number_increment,
            'number_next_actual': self.number_next_actual,
        })
        super(ResConfigSettingsInherit, self).set_values()
