# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError


class CreateOrDuplicateProjectWizard(models.TransientModel):
    _name = 'create.duplicate.project.crm.wizard'

    is_create_project = fields.Boolean(string="Create or Duplicate")
    wizard_project_id = fields.Many2one('project.project', string='Project')

    def create_duplicate_project(self):
        active_ids = self._context.get('active_ids')
        crm_lead_obj = self.env['crm.lead']
        project_project_obj = self.env['project.project']
        for active_id in active_ids:
            opportunity_obj = crm_lead_obj.browse(active_id)
            if opportunity_obj.project_id:
                raise UserError('There''s a project already attached to this opportunity.')
            elif opportunity_obj.type != 'opportunity':
                raise UserError('You can only create a project for an opportunity.')
            else:
                if not self.is_create_project:
                    vals = {
                        'name': opportunity_obj.name,
                        'stage_id': self.env['project.stage'].search([], limit=1),
                        'source': self.env['project.source'].search([], limit=1),
                        'project_num': opportunity_obj.project_num,
                        'type': 0,
                        'country': opportunity_obj.country.ids,
                        'company_id': opportunity_obj.company_id.id,
                        'partner_id': opportunity_obj.partner_id.id,
                        'start_date': opportunity_obj.start_date,
                        'opportunity_id': opportunity_obj.id,
                    }
                    project_copy = project_project_obj.create(vals)
                else:
                    project_copy = project_project_obj.browse(self.wizard_project_id.id).copy(
                        default={
                            'name': opportunity_obj.name,
                            'opportunity_id': opportunity_obj.id
                        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': project_copy.id,
            'view_mode': 'form',
        }
