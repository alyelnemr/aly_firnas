# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_required = fields.Boolean(string="Dates Required?", default=False)
