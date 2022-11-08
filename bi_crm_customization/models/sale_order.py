# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderCRMInherit(models.Model):
    _inherit = 'sale.order'

    def _set_default_standard_payment(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_payment_schedule')

    def _set_default_terms_conditions(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_terms_condition')

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(SaleOrderCRMInherit, self).default_get(fields)
        if self._context.get('active_id') or self.opportunity_id:

            lead = self.env['crm.lead'].browse(self._context['active_id'])
            result['name'] = 'convert'

            if 'project_name' in fields and lead.project_name:
                result['project_name'] = lead.project_name
            if 'client_name_id' in fields and lead.end_client:
                result['client_name_id'] = lead.end_client.ids
            if 'fund' in fields and lead.fund:
                result['fund'] = lead.fund.id
            if 'partnership_model' in fields and lead.partnership_model:
                result['partnership_model'] = lead.partnership_model.id
            if 'sub_type' in fields and lead.sub_type:
                result['sub_type'] = lead.sub_type.id
            if 'actual_sub_date' in fields and lead.actual_sub_date:
                result['actual_sub_date'] = lead.actual_sub_date
            if 'sub_date' in fields and lead.sub_date:
                result['sub_date'] = lead.sub_date
            if 'start_date' in fields and lead.start_date:
                result['start_date'] = lead.start_date
            if 'source_id' in fields and lead.source_id:
                result['source_id'] = lead.source_id.id
            if 'currency_id' in fields and lead.currency_id:
                result['currency_id'] = lead.currency_id.id
            if 'country' in fields and lead.country:
                result['country'] = lead.country.ids
            if 'partner' in fields and lead.partner:
                result['partner'] = lead.partner.ids
            if 'project_name' in fields and lead.project_name:
                result['project_name'] = lead.project_name
            if 'forecast' in fields and lead.forecast:
                result['forecast'] = lead.forecast
            if 'project_number' in fields and lead.project_num:
                result['project_number'] = lead.project_num
            if 'proposals_engineer_id' in fields and lead.proposals_engineer_id:
                result['proposals_engineer_id'] = lead.proposals_engineer_id.id
            if 'type_custom' in fields and lead.type_custom:
                result['type_custom'] = lead.type_custom.id
            if 'type_custom_ids' in fields and lead.type_custom_ids:
                result['type_custom_ids'] = lead.type_custom_ids.ids
            if 'internal_opportunity_name' in fields and lead.internal_opportunity_name:
                result['internal_opportunity_name'] = lead.internal_opportunity_name
            if 'rfp_ref_number' in fields and lead.rfp_ref_number:
                result['rfp_ref_number'] = lead.rfp_ref_number
            if 'subcontractor_supplier_ids' in fields and lead.subcontractor_supplier_ids:
                result['subcontractor_supplier_ids'] = lead.subcontractor_supplier_ids.ids
            if 'proposal_reviewer_ids' in fields and lead.proposal_reviewer_ids:
                result['proposal_reviewer_ids'] = lead.proposal_reviewer_ids.ids
            if 'latest_proposal_submission_date' in fields and lead.latest_proposal_submission_date:
                result['latest_proposal_submission_date'] = lead.latest_proposal_submission_date
            if 'result_date' in fields and lead.result_date:
                result['result_date'] = lead.result_date
            if 'contract_signature_date' in fields and lead.contract_signature_date:
                result['contract_signature_date'] = lead.contract_signature_date
            if 'initial_contact_date' in fields and lead.initial_contact_date:
                result['initial_contact_date'] = lead.initial_contact_date
            if 'analytic_account_id' in fields and lead.analytic_account_id:
                result['analytic_account_id'] = lead.analytic_account_id.id
            if 'analytic_tag_ids_for_analytic_account' in fields and lead.analytic_tag_ids_for_analytic_account:
                result['analytic_tag_ids'] = lead.analytic_tag_ids_for_analytic_account.ids
        return result

    project_name = fields.Char(string="Customer's Project Name / Proposal Title")
    document_name = fields.Char(string="Proposal Subject")
    file_name = fields.Char(string="Document/File  Name (Footer)")
    standard_payment_schedule = fields.Html(string="Standard Payment Schedule", default=_set_default_standard_payment)
    terms_and_conditions = fields.Html(string="Terms And Conditions", default=_set_default_terms_conditions)

    serial_num = fields.Char(string="Serial Number")
    project_number = fields.Char(string="Project Number", store=True, readonly=True)
    type_custom = fields.Many2one('crm.type', string="Project Type", required=False)
    internal_opportunity_name = fields.Char(string="Internal Opportunity Name", required=False)
    type_custom_ids = fields.Many2many('crm.type', relation='type_custom_saleorder_rel', column1='type_custom_ids_id',
                                       column2='type_custom_ids_crm_type_id', string="Secondary Project Types")
    country = fields.Many2many('res.country', string='Country')
    start_date = fields.Date(string="Request Date")
    actual_sub_date = fields.Date(string="Actual Submission Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    forecast = fields.Monetary(string="Forecast", store=True)
    # source = fields.Many2one('project.source', string="Source", store=True)
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    # partner = fields.Many2many('res.partner', string="Partner") #, related='opportunity_id.partner'
    partner = fields.Many2many('res.partner', string="JV Partners")
    client_name = fields.Many2many('client.name', string="End Client")
    client_name_id = fields.Many2many('res.partner', 'cleintname_saleorder_rel', string="End Client")
    subcontractor_supplier_ids = fields.Many2many('res.partner', 'saleorder_subcontractor_rel', string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many('res.partner', 'saleorder_prop_reviewer_rel', string="Proposal Reviewers")
    latest_proposal_submission_date = fields.Date(string="Latest Proposal Submission Date")
    result_date = fields.Date(string="Result Date")
    contract_signature_date = fields.Date(string="Contract/PO Signature Date")
    initial_contact_date = fields.Date(string="Initial Contact Date", required=False)
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
    partner_contact = fields.Many2one('res.partner', string='Customer Contact', required=False,
                                      domain="[('parent_id', '=', partner_id)]")
