# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import ast


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        if not self._context.get('ignore_write', False):
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
                if stage_id and stage_id.allow_create_project and not self.project_id:
                    raise UserError(_('Please create or duplicate project before changing to this stage.'))

            write_result = super(CrmLead, self).write(vals)

            return write_result
