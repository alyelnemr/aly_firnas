# -*-	coding:	utf-8	-*-
from odoo import api, fields, models


class ExpectedRevenue(models.Model):
    _name = 'expected.revenue'

    name = fields.Char(string='Name', store=True)
