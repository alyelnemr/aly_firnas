# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_downpayment_service = fields.Boolean('Is Downpayment Service', default=False)
    # default_code = fields.Char(
    #     'Internal Reference', compute='_compute_default_code',
    #     inverse='_set_default_code', store=True, copy=True)
    # description_sale = fields.Text(
    #     'Sales Description', translate=True, copy=False,
    #     help="A description of the Product that you want to communicate to your customers. "
    #          "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")
