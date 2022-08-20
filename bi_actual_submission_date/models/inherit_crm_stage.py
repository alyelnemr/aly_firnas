# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    mandatory_actual_sub = fields.Boolean(string="Mandatory Actual Submission Date")
