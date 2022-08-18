# -*- coding: utf-8 -*-
from odoo import api, fields, models


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
    type_custom = fields.Many2one('crm.type', string="Type", required=True)
    project_name = fields.Char(string="Customer's Project Name / Proposal Title", store=True, )
    country = fields.Many2many('res.country', string='Countries')
    start_date = fields.Date(string="Start Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Char(string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner = fields.Many2many('res.partner', string="Partner")
    client_name = fields.Many2many('res.partner', 'crmlead_client_rel', string="End Client")
    # client_name = fields.Many2many('client.name', string="End Client")
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
