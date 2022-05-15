# -*- coding: utf-8 -*-

from odoo import models


class Customers(models.Model):
    _inherit = ['res.partner']