# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClientName(models.Model):
    _name = 'client.name'

    name = fields.Char(string="Client")
