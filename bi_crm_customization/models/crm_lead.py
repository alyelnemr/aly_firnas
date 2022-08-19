# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
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
        res['context']['default_start_date'] = self.start_date
        res['context']['default_sub_date'] = self.sub_date
        res['context']['default_sub_type'] = self.sub_type.id
        res['context']['default_fund'] = self.fund.id
        res['context']['default_partnership_model'] = self.partnership_model.id
        res['context']['default_partner'] = self.partner.ids
        res['context']['default_client_name'] = self.client_name.ids
        res['context']['default_rfp_ref_number'] = self.rfp_ref_number
        res['context']['default_proposals_engineer_id'] = self.proposals_engineer_id.id
        return res

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=10, index=True, required=False,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    project_num = fields.Char(string="Project Number", store=True)
    type_custom = fields.Many2one('crm.type', string="Project Type", required=True)
    type_custom_ids = fields.Many2many('crm.type', string="Secondary Project Types", required=True)
    project_name = fields.Char(string="Customer's Project Name / Proposal Title", store=True, )
    country = fields.Many2many('res.country', string='Countries')
    start_date = fields.Date(string="Request Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    actual_sub_date = fields.Date(string="Actual Submission Date")
    mandatory_actual_sub = fields.Boolean(related='stage_id.mandatory_actual_sub',
                                          string="Mandatory Actual Submission Date", store=True)
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Char(string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner = fields.Many2many('res.partner', string="JV Partners")
    client_name = fields.Many2many('res.partner', 'crmlead_client_rel', string="End Client")
    subcontractor_supplier_ids = fields.Many2many('res.partner', 'crmlead_subcontractor_rel', string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many('res.partner', 'crmlead_prop_reviewer_rel', string="Proposal Reviewers")
    latest_proposal_submission_date = fields.Date(string="Latest Proposal Submission Date")
    result_date = fields.Date(string="Result Date")
    contract_signature_date = fields.Date(string="Contract/PO Signature Date")
    initial_contact_date = fields.Date(string="Initial Contact Date")
    # client_name = fields.Many2many('client.name', string="End Client")
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    forecast = fields.Monetary(string="Forecast", store=True)

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
