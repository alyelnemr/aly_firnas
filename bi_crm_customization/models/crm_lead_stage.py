# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class LeadStage(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "crm.leadstage"
    _description = "CRM Lead Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    @api.model
    def default_get(self, fields):
        """ Hack :  when going from the pipeline, creating a stage with a sales team in
            context should not create a stage for the current Sales Team only
        """
        ctx = dict(self.env.context)
        if ctx.get('default_team_id') and not ctx.get('crm_team_mono'):
            ctx.pop('default_team_id')
        return super(LeadStage, self.with_context(ctx)).default_get(fields)

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    is_won = fields.Boolean('Is Won Stage?')
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    team_id = fields.Many2one('crm.team', string='Sales Team', ondelete='set null',
        help='Specific team that uses this stage. Other teams will not be able to see or use this stage.')
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    mandatory_actual_sub = fields.Boolean(string="Mandatory Actual Submission Date")
    mandatory_currency = fields.Boolean(string="Mandatory Currency")
    mandatory_forecast = fields.Boolean(string="Mandatory Forecast")
    mandatory_result_date = fields.Boolean(string="Mandatory Result Date")
    mandatory_signature_date = fields.Boolean(string="Mandatory Contract/PO Signature Date")
    notify_group_ids = fields.Many2many('res.groups', string='Award Notification Groups', )
