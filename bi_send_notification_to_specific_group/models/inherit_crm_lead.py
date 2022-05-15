# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import ast

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.onchange('stage_id')
    def send_notification_mail_to_specific_group(self):
        # get_param = self.env['ir.config_parameter'].sudo().get_param
        notification_groups_ids = ast.literal_eval(
            (self.env['ir.config_parameter'].sudo().get_param('notification_groups_ids')))
        stage_id = ast.literal_eval(
            (self.env['ir.config_parameter'].sudo().get_param('stage_id')))
        partner_ids = []
        for group in self.env['res.groups'].search([('id', 'in', notification_groups_ids)]):
            for user in group.users:
                if user.partner_id.id not in partner_ids:
                    partner_ids.append(user.partner_id.id)
                    # print(stage_id)
        for line in self:
            if line.stage_id.id == stage_id:
                print(self.stage_id.id, stage_id)
                mail_content = "Dears,<br>Task " + line.name + " stage has been changed to " + line.stage_id.name +". <br> Best Regards."
                main_content = {
                    'subject': _('Task %s') % (line.name),
                    'recipient_ids': [(6, 0, partner_ids)],
                    'author_id': self.env.uid,
                    'body_html': mail_content,
                }
                mail = self.env['mail.mail'].create(main_content)
                mail.send()