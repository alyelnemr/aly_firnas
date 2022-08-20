# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    actual_sub_date = fields.Date(string="Actual Submission Date")
    mandatory_actual_sub = fields.Boolean(related='stage_id.mandatory_actual_sub',
                                          string="Mandatory Actual Submission Date", store=True)

    @api.onchange('stage_id')
    def _onchange_stages(self):
        for rec in self:
            if rec.stage_id.mandatory_actual_sub and not rec.actual_sub_date:
                raise ValidationError('Please Add Actual Submission Date First!')

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
