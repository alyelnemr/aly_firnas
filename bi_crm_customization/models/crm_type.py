# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CRMType(models.Model):
    _name = 'crm.type'

    name = fields.Char(string='Type Name', required=True)
    type_no = fields.Char(string='Type Number', required=True)
