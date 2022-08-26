# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'project.project'

    user_id = fields.Many2one('res.users', string='Project Engineer', default=lambda self: self.env.user, tracking=True)
    project_manager_id = fields.Many2one('res.users', string='Project Manager', tracking=True)
    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
        , copy=False)

    def action_view_opportunity(self):
        action = self.env.ref('crm.crm_lead_opportunities').read()[0]
        # operator = 'child_of' if self..is_company else '='
        action['domain'] = [('id', '=', self.opportunity_id.id), ('type', '=', 'opportunity')]
        action['view_mode'] = 'form'
        action['view_type'] = 'form'
        action['res_id'] = self.opportunity_id.id
        action['views'] = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
        return action
