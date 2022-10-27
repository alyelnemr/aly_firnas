# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import ast


class CRMLeadInherit(models.Model):
    _inherit = 'crm.lead'

    def action_new_quotation(self):
        res = super(CRMLeadInherit, self).action_new_quotation()
        res['context']['default_project_number'] = self.project_num
        res['context']['default_type_custom'] = self.type_custom
        res['context']['default_project_name'] = self.project_name
        res['context']['default_country'] = self.country.ids
        res['context']['default_country'] = self.country.ids
        res['context']['default_start_date'] = self.start_date
        res['context']['default_forecast'] = self.forecast
        res['context']['default_sub_date'] = self.sub_date
        res['context']['default_sub_type'] = self.sub_type.id
        res['context']['default_fund'] = self.fund.id
        res['context']['default_partnership_model'] = self.partnership_model.id
        res['context']['default_partner'] = self.partner.ids
        res['context']['default_end_client'] = self.end_client.ids
        res['context']['default_rfp_ref_number'] = self.rfp_ref_number
        res['context']['default_proposals_engineer_id'] = self.proposals_engineer_id.id
        return res

    def _default_team_id(self, user_id):
        domain = [('use_leads', '=', True)] if self._context.get('default_type') == "lead" or self.type == 'lead' else [
            ('use_opportunities', '=', True)]
        return self.env['crm.team']._get_default_team_id(user_id=user_id, domain=domain)

    def _default_leadstage_id(self):
        team = self._default_team_id(user_id=self.env.uid)
        return self._stage_find(team_id=team.id, domain=[('fold', '=', False)]).id

    @api.model
    def _read_group_leadstage_ids(self, stages, domain, order):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=10, index=True, required=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    type_custom = fields.Many2one('crm.type', string="Project Type", required=True)
    type_custom_ids = fields.Many2many(comodel_name='crm.type', relation='type_custom_crmlead_rel', column1='type_custom_ids_id',
                                       column2='type_custom_ids_crm_type_id', string="Secondary Project Types", required=False)
    project_name = fields.Char(string="Customer's Project Name / Proposal Title", store=True, )
    country = fields.Many2many(comodel_name='res.country', string='Countries')
    client_name = fields.Many2one('res.partner', string="End Client", help="deprecated, not used, you can use end_client field")
    start_date = fields.Date(string="Request Date", required=False)
    sub_date = fields.Datetime(string="Submission Deadline", required=True)
    actual_sub_date = fields.Date(string="Actual Submission Date")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Char(string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner = fields.Many2many(comodel_name='res.partner', string="JV Partners")
    subcontractor_supplier_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_subcontractor_rel', column1='subcontractor_id', column2='subcontractor_partner_id', string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_prop_reviewer_rel', column1='prop_reviewer_id',
                                             column2='prop_reviewer_partner_id',string="Proposal Reviewers")
    latest_proposal_submission_date = fields.Date(string="Latest Proposal Submission Date")
    result_date = fields.Date(string="Result Date")
    contract_signature_date = fields.Date(string="Contract/PO Signature Date")
    initial_contact_date = fields.Date(string="Initial Contact Date", required=True)
    end_client = fields.Many2many(comodel_name='res.partner', relation='crm2opprtunity_endclient_rel', column1='crm_end_client_id', column2='end_client_partner_id', string="End Client")
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    forecast = fields.Monetary(string="Forecast", store=True)
    name = fields.Char('Opportunity', default='/', index=True, compute='_compute_name', store=True)
    is_existing_opportunity = fields.Boolean(string='Is it an existing opportunity?')
    parent_opportunity_id = fields.Many2one('crm.lead', string='Existing Opportunities')
    serial_number = fields.Char(string='Serial Number')
    original_serial_number = fields.Char(string='Original Serial Number')
    letter_identifier = fields.Char(string='Letter Identifier')
    project_num = fields.Char(string="Project Number", default='/', compute='_compute_project_num', store=True)
    project_id = fields.Many2one('project.project', string="Project", compute='_compute_project_project', store=False)
    internal_opportunity_name = fields.Char(string="Internal Opportunity Name", required=True)
    next_letter_sequence = fields.Char(string="Next Letter Sequence", readonly=True)
    task_id = fields.Many2one('project.task', string="Task in Project Module", required=False, copy=False)
    actual_sub_date = fields.Date(string="Actual Submission Date")
    lead_stage_id = fields.Many2one('crm.leadstage', string='Lead Stage', tracking=True, copy=False)

    @api.depends('project_num', 'country.code', 'internal_opportunity_name')
    def _compute_name(self):
        for record in self:
            if record.project_num and record.country and record.internal_opportunity_name:
                countries_code = "-".join(record.country.mapped('code'))
                record.name = record.project_num + ' -' + countries_code + '- ' + record.internal_opportunity_name
            else:
                record.name = '/'

    @api.depends('serial_number', 'type_custom.type_no', 'letter_identifier')
    def _compute_project_num(self):
        for record in self:
            if record.type_custom:
                if record.letter_identifier:
                    record.project_num = (record.serial_number or '') + record.type_custom.type_no + record.letter_identifier
                else:
                    record.project_num = (record.serial_number or '') + record.type_custom.type_no
            else:
                record.project_num = '/'

    def _compute_project_project(self):
        for record in self:
            record.project_id = False
            project_id = self.env['project.project'].search([('opportunity_id', '=', record.id)])
            if project_id:
                record.project_id = project_id.id

    @api.model
    def create(self, vals):
        if vals.get('type') == 'opportunity' or self._context.get('default_type') == 'opportunity':
            if not vals.get('serial_number'):
                if vals.get('is_existing_opportunity'):
                    parent_opp = self.env['crm.lead'].browse(vals['parent_opportunity_id'])
                    vals['serial_number'] = parent_opp.serial_number

                    # parent opportunity next letter sequence
                    if vals.get('letter_identifier'):
                        next_letter_sequence = chr(ord(vals.get('letter_identifier')) + 1)
                        parent_opp.sudo().write({'next_letter_sequence': next_letter_sequence})
                else:
                    new_serial_no = self.env['ir.sequence'].next_by_code('bi_crm_concatenated_name.serial_no') or _(
                        'New')
                    vals['serial_number'] = new_serial_no

            vals['original_serial_number'] = vals['serial_number']

        res = super(CRMLeadInherit, self).create(vals)
        if res.type == 'opportunity':
            project = self.env['project.project'].search([('name', '=', 'Proposals Department')])
            task_id = self.env['project.task'].sudo().create({
                'name': res.name,
                'project_id': project.id,
                'user_id': res.proposals_engineer_id.id
            })
            res.task_id = task_id.id
        return res

    def write(self, vals):
        is_conversion = False
        if 'parent_opportunity_id' in vals:
            if self.type == 'opportunity':
                if vals['parent_opportunity_id']:
                    parent_opp = self.env['crm.lead'].browse(vals['parent_opportunity_id'])
                    vals['serial_number'] = parent_opp.serial_number
                # else:
                #     vals['serial_number'] = self.original_serial_number
        if 'type' in vals and self.type != vals['type']:
            is_conversion = True
        res = super(CRMLeadInherit, self).write(vals)
        if self.type == 'opportunity' and not self.task_id and is_conversion:
            project = self.env['project.project'].search([('name', '=', 'Proposals Department')])
            task_id = self.env['project.task'].sudo().create({
                'name': self.name,
                'project_id': project.id,
                'user_id': self.proposals_engineer_id.id
            })
            self.task_id = task_id
        if self.task_id and self.task_id.name != self.name:
            self.task_id.name = self.name
        if self.task_id and self.task_id.user_id != self.proposals_engineer_id:
            self.task_id.user_id = self.proposals_engineer_id
        return res

    def action_new_quotation(self):
        res = super(CRMLeadInherit, self).action_new_quotation()
        res['context']['default_type_custom'] = self.type_custom.name
        return res

    @api.onchange('is_existing_opportunity')
    def reset_parent_opportunity_id(self):
        if not self.is_existing_opportunity:
            self.parent_opportunity_id = False

    @api.onchange('parent_opportunity_id')
    def get_related_country(self):
        for rec in self:
            if rec.parent_opportunity_id and rec.parent_opportunity_id.country:
                rec.country = rec.parent_opportunity_id.country
            else:
                rec.country = False

            # parent opprtunity letter sequence
            if rec.parent_opportunity_id:
                rec.letter_identifier = rec.parent_opportunity_id.next_letter_sequence or 'B'
            else:
                rec.letter_identifier = False

    @api.onchange('stage_id')
    def _onchange_stages(self):
        err = ''
        for rec in self:
            if rec.stage_id.mandatory_actual_sub and not rec.actual_sub_date:
                err = 'Please Add Actual Submission Date First!\n'
            if rec.stage_id.mandatory_currency and not rec.currency_id:
                err += 'Please Add Currency!\n'
            if rec.stage_id.mandatory_forecast and rec.forecast <= 0:
                err += 'Please Add Forecast!\n'
            if rec.stage_id.mandatory_result_date and not rec.result_date:
                err += 'Please Add Result Date!\n'
            if rec.stage_id.mandatory_signature_date and not rec.contract_signature_date:
                err += 'Please Add Result Date!\n'
            if err:
                raise ValidationError(err)

    def _notify_submission_date_groups(self):
        # groups to notify
        date_sub_groups_ids = self.env['res.users'].browse(self.env.uid).company_id.date_sub_groups_ids.ids
        group_ids = self.env['res.groups'].sudo().search([('id', 'in', date_sub_groups_ids)])
        group_partner_ids = group_ids.users.mapped('partner_id')
        today_date = fields.Date.context_today(self)

        leads_need_notification_ids = self.env['crm.lead'].sudo().search(
            [('actual_sub_date', '!=', False), ('mandatory_actual_sub', '=', True),
             ('actual_sub_date', '<', today_date)]).filtered(
            lambda l: ((today_date - l.actual_sub_date).days + 1) % 7 == 0)
        if leads_need_notification_ids and group_partner_ids:
            for lead in leads_need_notification_ids:
                lead.message_post(
                    body=_(
                        "The Stage '%s' of this pipeline with actual submission date '%s' has not been Changed for the last 7 days, please follow up. <br> Best Regards.") % (
                             lead.stage_id.name, lead.actual_sub_date),
                    partner_ids=group_partner_ids.ids)

    def action_view_project(self):
        action = self.env.ref('project.open_view_project_all_config').read()[0]
        action['domain'] = [('id', '=', self.project_id.id)]
        action['view_mode'] = 'form'
        action['view_type'] = 'form'
        action['res_id'] = self.project_id.id
        action['view_id'] = self.env.ref('project.view_project').id
        return action
