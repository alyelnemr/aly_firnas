# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    notify_group_ids = fields.Many2many('res.groups', string='Award Notification Groups', )