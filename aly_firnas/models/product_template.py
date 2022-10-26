# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_downpayment_service = fields.Boolean('Is Downpayment Service', default=False)
