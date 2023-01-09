# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, http
from odoo.exceptions import ValidationError


class WHSelectOperationType(models.TransientModel):
    _name = 'wh.email.wizard'
    _description = 'Send Confirmation Email for WH Transaction'

    def _get_current_url(self):
        return http.request.httprequest.host_url

    partner_id = fields.Many2one('res.partner', 'User Email', required=True, domain=[('company_type', '=', 'person')])
    current_url = fields.Char('Current URL', default=lambda self: self._get_current_url())
    wh_url = fields.Char('WH URL')
    reject_url = fields.Char('Reject URL')
    approve_url = fields.Char('Approve URL')
    wh_id = fields.Many2one(
        'stock.picking', 'Source WH Transaction ID')

    def action_send_mail(self):
        records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for rec in records:
            wh_id = str(rec.id)
            self.wh_id = rec
            self.wh_url = self.current_url + 'web?#id=' + wh_id + '&model=' + self.env.context.get('active_model')
            self.approve_url = self.current_url + 'my/wh_confirmation_accept/' + wh_id
            self.reject_url = self.current_url + 'my/wh_confirmation_reject/' + wh_id
            rec.write({
                'approve_url': self.approve_url,
                'reject_url': self.reject_url,
                'user_to_approve_url': self.partner_id.id
            })
            partner_email = self.partner_id.email
            if not partner_email:
                raise ValidationError(_("Sorry, This user has no email defined."))
            template = self.env.ref('aly_firnas.aly_wh_mail_template')
            # template.email_from = self.env.user
            # template.email_to = partner_email
            email_values = {
                'subject': rec.name + ' Confirmation',
                'email_to': partner_email,
                'email_from': self.env.user.email,
            }
            template.send_mail(rec.id, force_send=True, email_values=email_values)
            rec.with_context(force_send=True).message_post_with_template(template.id,
                                                                         email_layout_xmlid='mail.mail_notification_light')
