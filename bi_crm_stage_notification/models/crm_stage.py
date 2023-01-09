# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    mandatory_actual_sub = fields.Boolean(string="Mandatory Actual Submission Date")
    mandatory_currency = fields.Boolean(string="Mandatory Currency")
    mandatory_forecast = fields.Boolean(string="Mandatory Forecast")
    mandatory_result_date = fields.Boolean(string="Mandatory Result Date")
    mandatory_signature_date = fields.Boolean(string="Mandatory Contract/PO Signature Date")
    allow_create_project = fields.Boolean(string="Allow to create Project")
    notify_group_ids = fields.Many2many('res.groups', string='Award Notification Groups', )