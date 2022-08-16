from odoo import models, fields, api, _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    is_existing_opportunity = fields.Boolean(string='Is it an existing opportunity?')
    parent_opportunity_id = fields.Many2one('crm.lead', string='Existing Opportunities')
    serial_number = fields.Char(string='Serial Number')
    original_serial_number = fields.Char(string='Original Serial Number')
    type_custom = fields.Many2one('crm.type', string="Type", required=True)
    letter_identifier = fields.Char(string='Letter Identifier')
    project_num = fields.Char(string="Project Number", default='/', compute='_compute_project_num', store=True)
    internal_opportunity_name = fields.Char(string="Internal Opportunity Name", required=True)
    next_letter_sequence = fields.Char(string="Next Letter Sequence", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    forecast = fields.Monetary(string="Forecast", store=True)
    partner_id = fields.Many2one('res.partner', string='Customer', index=True, required=False,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    project_num = fields.Char(string="Project Number", store=True)
    type_custom = fields.Char(string="Type")
    project_name = fields.Char(string="Customer's Project Name / Proposal Title", store=True, )
    country = fields.Many2many('res.country', string='Countries')
    start_date = fields.Date(string="Start Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Char(string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner_ids = fields.Many2many('res.partner', string="Partner")
    client_name = fields.Many2many('res.partner', 'crmlead_client_rel', string="End Client")
    # client_name = fields.Many2many('client.name', string="End Client")
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    source_id = fields.Many2one('utm.source', string='Source', required=True, ondelete='cascade',
                                help="This is the link source, e.g. Search Engine, another domain, or name of email list")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if self._context.get('active_id'):

            lead = self.env['crm.lead'].browse(self._context['active_id'])

            if 'client_name' in fields and lead.client_name:
                result['client_name'] = lead.client_name
            if 'fund' in fields and lead.fund:
                result['fund'] = lead.fund
            if 'partnership_model' in fields and lead.partnership_model:
                result['partnership_model'] = lead.partnership_model
            if 'sub_type' in fields and lead.sub_type:
                result['sub_type'] = lead.sub_type.id
            if 'sub_date' in fields and lead.sub_date:
                result['sub_date'] = lead.sub_date
            if 'start_date' in fields and lead.start_date:
                result['start_date'] = lead.start_date
            if 'source_id' in fields and lead.source_id:
                result['source_id'] = lead.source_id.id
            if 'country' in fields and lead.country:
                result['country'] = lead.country.ids
            if 'partner_ids' in fields and lead.partner:
                result['partner_ids'] = lead.partner.ids
            if 'project_name' in fields and lead.project_name:
                result['project_name'] = lead.project_name
            if 'project_num' in fields and lead.project_num:
                result['project_num'] = lead.project_num
            if 'proposals_engineer_id' in fields and lead.proposals_engineer_id:
                result['proposals_engineer_id'] = lead.proposals_engineer_id.id
            if 'type_custom' in fields and lead.type_custom:
                result['type_custom'] = lead.type_custom
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
            new_serial_no = self.env['ir.sequence'].next_by_code('bi_crm_concatenated_name.serial_no') or _('New')
            lead.update({
                'serial_number': new_serial_no,
                'original_serial_number': new_serial_no,
                'is_existing_opportunity': self.is_existing_opportunity,
                'partner_id': self.partner_id.id,
                'partner': self.partner_ids.ids,
                'forecast': self.forecast,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'project_name': self.project_name,
                'client_name': self.client_name,
                'country': self.country,
                'fund': self.fund,
                'internal_opportunity_name': self.internal_opportunity_name,
                'letter_identifier': self.letter_identifier,
                'next_letter_sequence': self.next_letter_sequence,
                'parent_opportunity_id': self.parent_opportunity_id.id,
                'original_serial_number': self.original_serial_number,
                'partnership_model': self.partnership_model,
                'project_num': self.project_num,
                'proposals_engineer_id': self.proposals_engineer_id.id,
                'rfp_ref_number': self.rfp_ref_number,
                'serial_number': self.serial_number,
                'source_id': self.source_id.id,
                'start_date': self.start_date,
                'sub_date': self.sub_date,
                'sub_type': self.sub_type,
                'type_custom': self.type_custom,
            })

        return leads[0].redirect_lead_opportunity_view()
