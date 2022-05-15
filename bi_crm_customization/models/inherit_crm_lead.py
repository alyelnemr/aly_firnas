# -*-	coding:	utf-8	-*-
from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    forecast = fields.Monetary(string="Forecast", store=True)
