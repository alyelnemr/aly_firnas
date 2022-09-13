# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def name_get(self):
        return [(item.id, '%s (%s)' % (item.name, item.ref) if item.ref else '%s' % item.name) for item in self]

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        domain = args + ['|', ('name', operator, name), ('ref', operator, name)]
        model_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(model_ids).with_user(name_get_uid))
