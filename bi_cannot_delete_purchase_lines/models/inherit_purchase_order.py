# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InheritPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def unlink(self):
        for rec in self:
            if rec.is_origin_so:
                raise UserError(_('Cannot delete a purchase order Line comes from SO.'))
        return super(InheritPurchaseOrderLine, self).unlink()
