# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    # project_partner = fields.Many2one('res.partner', related='project_id.partner_id', store=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 required=True,
                                 default=lambda self: self._get_default_partner(),
                                 related='project_id.partner_id',
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 store=True)

    old_deadline = fields.Date()

    # @api.onchange('date_deadline')
    # def _onchange_deadline(self):
    #     res = {}
    #     if self.date_deadline:
    #         res = {'warning': {
    #             'title': _('Warning'),
    #             'message': _('Task deadline changed to %s') % self.date_deadline}
    #         }
    #     if res:
    #         return res

    # @api.onchange('date_deadline')
    # def onchange_deadline(self):
    #     template_id = self.env.ref('bi_new_customized_fields.mail_template_deadline_project_task').id
    #     print(template_id)
    #     receipts_groups_ids = (self.env['ir.config_parameter'].sudo().get_param(
    #         'bi_new_customized_fields.group_date_deadline_notification'))
    #     template = self.env['mail.template'].browse(template_id)
    #     template.send_mail(self, ['user_id'])

    # @api.onchange('date_deadline')
    # def action_mail_send(self):
    #     mail_compose = self.env['mail.compose.message']
    #     template_id = self.env.ref('bi_new_customized_fields.mail_template_deadline_project_task')
    #     ctx = dict()
    #     ctx.update(
    #         {'default_model': 'project.task', 'default_res_id': self.ids[0], 'default_use_template': bool(template_id),
    #          'default_template_id': template_id.id, 'default_composition_mode': 'comment',
    #          'mark_so_as_sent': True, })
    #     receipts_groups_ids = (self.env['ir.config_parameter'].sudo().get_param(
    #         'bi_new_customized_fields.group_date_deadline_notification'))
    #     new_message = mail_compose.with_context(ctx).create(
    #         {'partner_ids': receipts_groups_ids, 'body': template_id.body_html, })
    #     new_message.send_mail()
    #     template_id.send_mail(self.ids[0], force_send=True)

    def write(self, vals):
        res = super(ProjectTaskInherit, self).write(vals)
        for record in self:
            if record.date_deadline != record.old_deadline:
                record.old_deadline = record.date_deadline
                record.passport_mail_reminder()
        return res

    def passport_mail_reminder(self):
        # receipts_groups_ids = self.env.user.has_group('bi_new_customized_fields.group_date_deadline_notification')
        for user in self:
            if self.date_deadline:
                mail_content = "Dear '" + str(user.user_id.name) + "',<br>The deadline of your task '" + str(
                    user.name) + "' has changed to '" + str(user.date_deadline) + "'. <br> Best Regards."
                main_content = {
                    'subject': _('Warning: Task Deadline'),
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': user.user_id.email,
                }
                self.env['mail.mail'].create(main_content).send()
