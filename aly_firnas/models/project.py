# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProjectProject(models.Model):
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

    @api.model
    def create(self, values):
        """ Create an analytic account if project allow timesheet and don't provide one
            Note: create it before calling super() to avoid raising the ValidationError from _check_allow_timesheet
        """
        allow_old = values['allow_timesheets']
        values['allow_timesheets'] = False
        res = super(ProjectProject, self).create(values)
        res.allow_timesheets = allow_old
        return res

    @api.model
    def _create_analytic_account_from_values(self, values):
        analytic_account = self.env['account.analytic.account'].search([('name', '=', 'Template')], limit=1)
        return analytic_account
    #
    # @api.model
    # def _create_analytic_account_from_values(self, values):
    #     # analytic_account = self.env['account.analytic.account'].create({
    #     #     'name': values.get('name', _('Unknown Analytic Account')),
    #     #     'company_id': values.get('company_id') or self.env.company.id,
    #     #     'partner_id': values.get('partner_id'),
    #     #     'active': True,
    #     # })
    #     return False

    def _create_analytic_account(self):
        return
