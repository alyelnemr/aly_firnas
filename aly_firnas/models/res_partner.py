# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')], default='draft', string='Status', copy=False)

    @api.model
    def default_get(self, fields):
        vals = super(ResPartnerInherit, self).default_get(fields)
        vals['state'] = 'draft'
        return vals

    def write(self, vals):
        if 'state' in vals:
            has_my_group = self.env.user.has_group('aly_firnas.group_update_partner_state')
            if not has_my_group:
                raise ValidationError("Sorry you can't edit state for partners!")
        return super(ResPartnerInherit, self).write(vals)
