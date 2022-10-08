# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        has_my_group = self.env.user.has_group(
            'bi_security_creation.group_create_partners')
        if not has_my_group:
            raise exceptions.ValidationError(
                "Sorry you can't create partners!")
        return super(ResPartnerInherit, self).create(vals)

    def write(self, vals):
        if ('name' or 'company_id' or 'display_name' or 'date' or 'title' or 'parent_id' or 'lang' or 'user_id' or 'vat' or 'website' or 'active' or 'type' or 'street' or 'street2' or 'zip' or 'city' or 'state_id' or 'country_id' or 'partner_latitude' or 'partner_longitude' or 'email' or 'phone' or 'mobile' or 'is_company' or 'industry_id' or 'commercial_partner_id' or 'commercial_company_name' or 'company_name' or 'additional_info' or 'fax' or 'function') in vals:
            has_my_group = self.env.user.has_group(
                'bi_security_creation.group_create_partners')
            if not has_my_group:
                raise exceptions.ValidationError(
                    "Sorry you can't edit partners!")
        return super(ResPartnerInherit, self).write(vals)
