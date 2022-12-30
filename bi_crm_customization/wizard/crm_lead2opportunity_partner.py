from odoo import models, fields, api, _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True, copy=False)
    is_existing_opportunity = fields.Boolean(string='Is it an existing opportunity?')
    parent_opportunity_id = fields.Many2one('crm.lead', string='Existing Opportunities')
    serial_number = fields.Char(string='Serial Number')
    original_serial_number = fields.Char(string='Original Serial Number')
    type_custom = fields.Many2one('crm.type', string="Project Type", required=False)
    letter_identifier = fields.Char(string='Letter Identifier')
    project_num = fields.Char(string="Project Number", default='/', compute='_compute_project_num', store=True)
    internal_opportunity_name = fields.Char(string="Internal Opportunity Name", required=False)
    next_letter_sequence = fields.Char(string="Next Letter Sequence", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    forecast = fields.Monetary(string="Forecast", store=True)
    partner_id = fields.Many2one('res.partner', string='Customer', index=True, required=False,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    type_custom_ids = fields.Many2many(comodel_name='crm.type', relation='type_custom_oppor_crmlead_rel', column1='type_custom_ids_oppor_id', column2='type_custom_ids_oppor_crm_type_id',
                                       string="Secondary Project Types", required=False)
    project_name = fields.Char(string="Customer's Project Name / Proposal Title", store=True, )
    country = fields.Many2many('res.country', string='Countries', store=True, required=True)
    start_date = fields.Date(string="Request Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    actual_sub_date = fields.Date(string="Actual Submission Date")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Char(string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner_ids = fields.Many2many('res.partner', string="JV Partners")
    subcontractor_supplier_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_oppor_subcontractor_rel', column1='subctractor_oppor_id', column2='subcontractor_oppor_partner_id', string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_prop_reviewer_oppor_rel',
                                             column1='prop_reviewer_oppor_id', column2='prop_reviewer_oppor_partner_id', string="Proposal Reviewers")
    latest_proposal_submission_date = fields.Date(string="Latest Proposal Submission Date")
    contract_signature_date = fields.Date(string="Contract/PO Signature Date")
    initial_contact_date = fields.Date(string="Initial Contact Date", required=False)
    result_date = fields.Date(string="Result Date")
    end_client = fields.Many2many(comodel_name='res.partner', relation='crm2opportunity_end_client_rel', column1='crm2opp_end_client_id', column2='endclient_partner_id',
                                  string="End Client")
    proposals_engineer_ids = fields.Many2many(comodel_name='res.users', relation='crm2opport_prop_eng_rel',
                                              column1='crm_prop_eng_id', column2='prop_eng_user_id', string="Secondary Proposals Engineers")
    proposals_engineer_id = fields.Many2one('res.users', string='Primary Proposals Engineer', required=True)
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    source_id = fields.Many2one('utm.source', string='Source', required=True, ondelete='cascade',
                                help="This is the link source, e.g. Search Engine, another domain, or name of email list")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)

    @api.onchange('parent_opportunity_id')
    def get_related_country(self):
        for rec in self:
            if rec.parent_opportunity_id and rec.parent_opportunity_id.country and not rec.country:
                rec.country = rec.parent_opportunity_id.country
            else:
                rec.country = False if not rec.country else rec.country
            # parent opprtunity letter sequence
            if rec.parent_opportunity_id:
                rec.letter_identifier = rec.parent_opportunity_id.next_letter_sequence or 'B'
            else:
                rec.letter_identifier = False

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

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if self._context.get('active_id'):

            lead = self.env['crm.lead'].browse(self._context['active_id'])
            result['name'] = 'convert'

            if 'end_client' in fields and lead.end_client:
                result['end_client'] = lead.end_client.ids
            if 'fund' in fields and lead.fund:
                result['fund'] = lead.fund.id
            if 'partnership_model' in fields and lead.partnership_model:
                result['partnership_model'] = lead.partnership_model.id
            if 'sub_type' in fields and lead.sub_type:
                result['sub_type'] = lead.sub_type.id
            if 'sub_date' in fields and lead.sub_date:
                result['sub_date'] = lead.sub_date
            if 'actual_sub_date' in fields and lead.actual_sub_date:
                result['actual_sub_date'] = lead.actual_sub_date
            if 'start_date' in fields and lead.start_date:
                result['start_date'] = lead.start_date
            if 'source_id' in fields and lead.source_id:
                result['source_id'] = lead.source_id.id
            if 'country' in fields and lead.country:
                result['country'] = lead.country.ids
            if 'partner_ids' in fields and lead.partner:
                result['partner_ids'] = lead.partner.ids
            if 'subcontractor_supplier_ids' in fields and lead.subcontractor_supplier_ids:
                result['subcontractor_supplier_ids'] = lead.subcontractor_supplier_ids.ids
            if 'proposal_reviewer_ids' in fields and lead.proposal_reviewer_ids:
                result['proposal_reviewer_ids'] = lead.proposal_reviewer_ids.ids
            if 'latest_proposal_submission_date' in fields and lead.latest_proposal_submission_date:
                result['latest_proposal_submission_date'] = lead.latest_proposal_submission_date
            if 'contract_signature_date' in fields and lead.contract_signature_date:
                result['contract_signature_date'] = lead.contract_signature_date
            if 'initial_contact_date' in fields and lead.initial_contact_date:
                result['initial_contact_date'] = lead.initial_contact_date
            if 'result_date' in fields and lead.result_date:
                result['result_date'] = lead.result_date
            if 'project_name' in fields and lead.project_name:
                result['project_name'] = lead.project_name
            if 'project_num' in fields and lead.project_num:
                result['project_num'] = lead.project_num
            if 'proposals_engineer_id' in fields and lead.proposals_engineer_id:
                result['proposals_engineer_id'] = lead.proposals_engineer_id.id
            if 'proposals_engineer_ids' in fields and lead.proposals_engineer_ids:
                result['proposals_engineer_ids'] = lead.proposals_engineer_ids.ids
            if 'type_custom' in fields and lead.type_custom:
                result['type_custom'] = lead.type_custom.id
            if 'type_custom_ids' in fields and lead.type_custom_ids:
                result['type_custom_ids'] = lead.type_custom_ids.ids
            if 'internal_opportunity_name' in fields and lead.internal_opportunity_name:
                result['internal_opportunity_name'] = lead.internal_opportunity_name
            if 'rfp_ref_number' in fields and lead.rfp_ref_number:
                result['rfp_ref_number'] = lead.rfp_ref_number
        return result

    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        values = {
            'team_id': self.team_id.id,
        }

        if self.partner_id:
            values['partner_id'] = self.partner_id.id

        if self.name == 'merge':
            leads = self.with_context(active_test=False).opportunity_ids.merge_opportunity()
            if not leads.active:
                leads.write({'active': True, 'activity_type_id': False, 'lost_reason': False})
            if leads.type == "lead":
                values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
                self.with_context(active_ids=leads.ids)._convert_opportunity(values)
            elif not self._context.get('no_force_assignation') or not leads.user_id:
                values['user_id'] = self.user_id.id
                leads.write(values)
        else:
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
            self._convert_opportunity(values)

        for lead in leads:
            if self.is_existing_opportunity:
                parent_opp = self.env['crm.lead'].browse(self.parent_opportunity_id.id)
                new_serial_no = parent_opp.serial_number

                # parent opportunity next letter sequence
                if self.letter_identifier:
                    next_letter_sequence = chr(ord(self.letter_identifier) + 1)
                    parent_opp.sudo().write({'next_letter_sequence': next_letter_sequence})
            else:
                new_serial_no = self.env['ir.sequence'].next_by_code('bi_crm_concatenated_name.serial_no') or _(
                    'New')
            lead.write({
                'serial_number': new_serial_no,
                'original_serial_number': new_serial_no,
                'is_existing_opportunity': self.is_existing_opportunity,
                'partner_id': self.partner_id.id,
                'partner': self.partner_ids.ids,
                'forecast': self.forecast,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'project_name': self.project_name,
                'end_client': self.end_client.ids,
                'country': self.country.ids,
                'fund': self.fund.id,
                'internal_opportunity_name': self.internal_opportunity_name,
                'letter_identifier': self.letter_identifier,
                'next_letter_sequence': self.next_letter_sequence,
                'parent_opportunity_id': self.parent_opportunity_id.id,
                'partnership_model': self.partnership_model,
                'project_num': self.project_num,
                'proposals_engineer_id': self.proposals_engineer_id.id,
                'proposals_engineer_ids': self.proposals_engineer_ids.ids,
                'rfp_ref_number': self.rfp_ref_number,
                'source_id': self.source_id.id,
                'start_date': self.start_date,
                'sub_date': self.sub_date,
                'sub_type': self.sub_type,
                'type_custom': self.type_custom.id,
                'type_custom_ids': self.type_custom_ids.ids,
                'is_analytic_account_id_created': False,
                'analytic_tag_ids_for_analytic_account': self.analytic_tag_ids.ids,
            })
            if lead.type_custom:
                if lead.letter_identifier:
                    lead.project_num = (lead.serial_number or '') + lead.type_custom.type_no + lead.letter_identifier
                else:
                    lead.project_num = (lead.serial_number or '') + lead.type_custom.type_no
            else:
                lead.project_num = '/'
            if lead.project_num and lead.country and lead.internal_opportunity_name:
                countries_code = "-".join(lead.country.mapped('code'))
                lead.name = lead.project_num + ' -' + countries_code + '- ' + lead.internal_opportunity_name
            else:
                lead.name = '/'

        return leads[0].redirect_lead_opportunity_view()


class Lead2OpportunityMassConvert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    end_client = fields.Many2many('res.partner', 'crm2opportunity_mass_end_client_rel', 'crm2opp_mass_end_client_id',
                                  'endclient_mass_partner_id',
                                  string="End Client")
    type_custom_ids = fields.Many2many('crm.type', 'type_custom_mass_crmlead_rel', 'type_custom_ids_mass_oppor_id',
                                       'type_custom_ids_mass_oppor_crm_type_id',
                                       string="Secondary Project Types", required=False)
    subcontractor_supplier_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_oppor_mass_subcontractor_rel',
                                                  column1='subctractor_oppor_mass_id', column2='subcontractor_oppor_mass_partner_id',
                                                  string="Subcontractors/Suppliers")
    proposal_reviewer_ids = fields.Many2many(comodel_name='res.partner', relation='crmlead_prop_reviewer_oppor_mass_rel',
                                             column1='prop_reviewer_oppor_mass_id', column2='prop_reviewer_oppor_mass_partner_id',
                                             string="Proposal Reviewers")
    proposals_engineer_ids = fields.Many2many(comodel_name='res.users', relation='crm2opport_mass_prop_eng_rel',
                                              column1='crm_prop_eng_id', column2='prop_eng_user_id', string="Proposals Engineers")
