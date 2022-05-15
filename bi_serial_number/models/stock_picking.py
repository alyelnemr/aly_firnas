# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for record in self:
            picking_name = record.name
            for move in record.move_ids_without_package:
                product_name = move.product_id.name
                for line in move.move_line_nosuggest_ids:
                    if (line.product_dates_required is True) and (line.product_tracking == 'serial') \
                            and (not line.lot_id and not line.calibration_date):
                        raise ValidationError(
                            _("Please insert a calibration date for [%s] lines in picking [%s].") %
                            (product_name, picking_name))
        res = super(StockPicking, self).button_validate()
        return res
