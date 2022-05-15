# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        # stage change: send notification to associated groups
        if 'stage_id' in vals:
            stage_id = self.env['crm.stage'].browse(vals['stage_id'])
            if stage_id and stage_id.notify_group_ids:
                group_partner_ids = stage_id.notify_group_ids.users.mapped('partner_id')
                self.message_post(
                    body=_(
                        "Stage Changed From '%s' To '%s'") % (
                             self.stage_id.name, stage_id.name),
                    partner_ids=group_partner_ids.ids)

        write_result = super(CrmLead, self).write(vals)

        return write_result
