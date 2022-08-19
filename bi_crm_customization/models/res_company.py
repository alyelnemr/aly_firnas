# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast


class ResCompany(models.Model):
    _inherit = 'res.company'

    date_sub_groups_ids = fields.Many2many('res.groups', string='Notification Groups')
