# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    fax = fields.Char(string="Fax Number")
