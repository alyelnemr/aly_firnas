# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    lot_description = fields.Char(string='Lot Description')
    lot_ref = fields.Char(string='Lot Internal Reference')

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        res.update({
            "account_analytic_id": self.group_id.sale_id.analytic_account_id.id,
            "analytic_tag_ids": self.group_id.sale_id.analytic_tag_ids.ids,
            "is_origin_so": True,
        })
        return res

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                    debit_account_id,
                                                                    credit_account_id, description)

        if self.picking_id.analytic_account_id:
            res['debit_line_vals']['analytic_account_id'] = self.picking_id.analytic_account_id.id
            res['credit_line_vals']['analytic_account_id'] = self.picking_id.analytic_account_id.id

        if self.picking_id.analytic_tag_ids:
            res['debit_line_vals']['analytic_tag_ids'] = self.picking_id.analytic_tag_ids.ids
            res['credit_line_vals']['analytic_tag_ids'] = self.picking_id.analytic_tag_ids.ids

        return res

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['description_picking'] = vals['name']

        res = super(StockMove, self).create(vals)
        return res

    def _get_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.

        HACK: This is needed while https://github.com/odoo/odoo/pull/29983
        is not merged.
        """
        price_unit = False
        po_line = self.purchase_line_id.sudo()
        if po_line and self.product_id == po_line.product_id:
            price = po_line._get_discounted_price_unit()
            if price != po_line.price_unit:
                # Only change value if it's different
                price_unit = po_line.price_unit
                po_line.sudo().price_unit = price
        res = super()._get_price_unit()
        if price_unit:
            po_line.sudo().price_unit = price_unit
        return res

    def _generate_serial_move_line_commands(self, lot_names, origin_move_line=None):
        """Return a list of commands to update the move lines (write on
        existing ones or create new ones).
        Called when user want to create and assign multiple serial numbers in
        one time (using the button/wizard or copy-paste a list in the field).

        :param lot_names: A list containing all serial number to assign.
        :type lot_names: list
        :param origin_move_line: A move line to duplicate the value from, default to None
        :type origin_move_line: record of :class:`stock.move.line`
        :return: A list of commands to create/update :class:`stock.move.line`
        :rtype: list
        """
        self.ensure_one()

        # Select the right move lines depending of the picking type configuration.
        move_lines = self.env['stock.move.line']
        if self.picking_type_id.show_reserved:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)
        else:
            move_lines = self.move_line_nosuggest_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)

        if origin_move_line:
            location_dest = origin_move_line.location_dest_id
        else:
            location_dest = self.location_dest_id._get_putaway_strategy(self.product_id)
        move_line_vals = {
            'picking_id': self.picking_id.id,
            'location_dest_id': location_dest.id or self.location_dest_id.id,
            'location_id': self.location_id.id,
            'lot_description': self.description_picking,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'qty_done': 1,
        }
        if origin_move_line:
            # `owner_id` and `package_id` are taken only in the case we create
            # new move lines from an existing move line. Also, updates the
            # `qty_done` because it could be usefull for products tracked by lot.
            move_line_vals.update({
                'owner_id': origin_move_line.owner_id.id,
                'package_id': origin_move_line.package_id.id,
                'qty_done': origin_move_line.qty_done or 1,
            })

        move_lines_commands = []
        for lot_name in lot_names:
            # We write the lot name on an existing move line (if we have still one)...
            if move_lines:
                move_lines_commands.append((1, move_lines[0].id, {
                    'lot_name': lot_name,
                    'qty_done': 1,
                }))
                move_lines = move_lines[1:]
            # ... or create a new move line with the serial name.
            else:
                move_line_cmd = dict(move_line_vals, lot_name=lot_name)
                move_lines_commands.append((0, 0, move_line_cmd))
        return move_lines_commands
