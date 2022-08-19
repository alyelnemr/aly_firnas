# -*-	coding:	utf-8	-*-
from odoo import api, fields, models
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    date_sub_groups_ids = fields.Many2many(related='company_id.date_sub_groups_ids', string='Notification Groups',
                                           readonly=False)
