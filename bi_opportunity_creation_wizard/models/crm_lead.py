# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CRMLeadInherit(models.Model):
    _inherit = 'crm.lead'

    def create_opportunity(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Opportunity',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'crm.lead',
            'context': {
                'default_type': 'opportunity',
            },
        }
