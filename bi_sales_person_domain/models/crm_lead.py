# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    user_id = fields.Many2one('res.users', string='Opportunity Manager', index=True, tracking=True,
                              default=lambda self: self.env.user)
