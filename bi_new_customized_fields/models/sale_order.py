# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def _set_default_standard_payment(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_payment_schedule')

    def _set_default_terms_conditions(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_terms_condition')

    project_name = fields.Char(string="Customer's Project Name / Proposal Title")
    document_name = fields.Char(string="Proposal Subject")
    file_name = fields.Char(string="Document/File  Name (Footer)")
    standard_payment_schedule = fields.Html(string="Standard Payment Schedule", default=_set_default_standard_payment)
    terms_and_conditions = fields.Html(string="Terms And Conditions", default=_set_default_terms_conditions)

    serial_num = fields.Char(string="Serial Number")
    project_number = fields.Char(string="Project Number", store=True)
    type_custom = fields.Many2one('crm.type', related='opportunity_id.type_custom', string="Project Type", required=True)
    type_custom_ids = fields.Many2many('crm.type', related='opportunity_id.type_custom_ids', string="Secondary Project Types", required=True)
    country = fields.Many2many('res.country', string='Country')
    start_date = fields.Date(related='opportunity_id.start_date', string="Request Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Many2one('project.source', string="Source", store=True)
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    # partner = fields.Many2many('res.partner', string="Partner") #, related='opportunity_id.partner'
    partner = fields.Many2many('res.partner', related='opportunity_id.partner', string="JV Partners")
    client_name = fields.Many2many('client.name', string="End Client")
    client_name_id = fields.Many2many('res.partner', related='opportunity_id.client_name', string="End Client")
    subcontractor_supplier_ids = fields.Many2many('res.partner', 'saleorder_subcontractor_rel', related='opportunity_id.subcontractor_supplier_ids',
                                                  string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many('res.partner', 'saleorder_prop_reviewer_rel',
                                             related='opportunity_id.proposal_reviewer_ids',string="Proposal Reviewers")
    latest_proposal_submission_date = fields.Date(related='opportunity_id.latest_proposal_submission_date',string="Latest Proposal Submission Date")
    result_date = fields.Date(related='opportunity_id.result_date',string="Result Date")
    contract_signature_date = fields.Date(related='opportunity_id.contract_signature_date',string="Contract/PO Signature Date")
    initial_contact_date = fields.Date(related='opportunity_id.initial_contact_date',string="Initial Contact Date")
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
