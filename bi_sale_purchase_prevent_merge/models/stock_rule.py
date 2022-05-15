# -*- coding: utf-8 -*-

from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        """ Avoid to merge two RFQ."""
        domain = super(StockRule, self)._make_po_get_domain(company_id, values, partner)
        domain += (('id', '=', 0),)
        return domain
