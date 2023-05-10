# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLineSection(models.Model):
    _name = "sale.order.line.section"

    name = fields.Char(string="Section Name")
