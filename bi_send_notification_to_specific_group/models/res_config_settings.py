# -*-	coding:	utf-8	-*-
from odoo import api, fields, models
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notification_groups_ids = fields.Many2many(comodel_name='res.groups',
                                               relation='notification_groups_rel',
                                               column1='sett_id',
                                               column2='grp_id', string='Mail Notifications Groups', store=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', store=True)

    def set_values(self):
        set_param = self.env['ir.config_parameter'].set_param
        set_param('notification_groups_ids', self.notification_groups_ids.ids)
        set_param('stage_id', self.stage_id.id)
        super(ResConfigSettings, self).set_values()

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        notification_groups_ids = get_param('notification_groups_ids')
        stage_id = get_param('stage_id')
        if notification_groups_ids:
            res.update(
                notification_groups_ids=ast.literal_eval(notification_groups_ids),
            )
        if stage_id:
            res.update(
                stage_id=ast.literal_eval(stage_id),
            )
        return res
