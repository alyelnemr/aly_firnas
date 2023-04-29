# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner.bank'

    iban = fields.Char('IBAN', required=False)
    swift = fields.Char('Swift', required=False)