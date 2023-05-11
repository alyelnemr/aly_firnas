# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero
import textile
from odoo.tools.misc import formatLang, get_lang
from functools import partial
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
