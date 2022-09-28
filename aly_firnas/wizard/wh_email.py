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
        lines = []
        records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for rec in records:
            wh_id = str(rec.id)
            self.wh_id = rec
            self.wh_url = self.current_url + 'web?#id=' + wh_id + '&model=' + self.env.context.get('active_model')
            self.approve_url = self.current_url + 'my/wh_confirmation_accept/' + wh_id
            self.reject_url = self.current_url + 'my/wh_confirmation_reject/' + wh_id
            partner_email = self.partner_id.email
            if not partner_email:
                raise ValidationError(_("Sorry, This user has no email defined."))
            template = self.env.ref('aly_firnas.aly_wh_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
