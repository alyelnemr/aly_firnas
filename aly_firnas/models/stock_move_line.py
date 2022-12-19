from collections import Counter

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import OrderedSet
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
import json


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('location_id', 'product_id')
    def _compute_lot_domain(self):
        for rec in self:
            rec.lot_id_domain = []
            rec.lot_id = False
            if rec.product_id:
                if rec.move_id.picking_type_id not in ['incoming']:
                    current_domain = [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                                      ('location_id', '=', rec.location_id.id)]
                    quant = self.env['stock.quant'].search(current_domain)
                    ids = quant.lot_id.ids or []
                    # if ids:
                    rec.lot_id_domain = json.dumps(
                        [('id', 'in', ids)]
                    )

    lot_description = fields.Char(string='Lot Description')
    lot_ref = fields.Char(string='Lot Internal Reference')
    calibration_date = fields.Date(string="Calibration Date")
    product_dates_required = fields.Boolean(string="bol", related="product_id.is_required")
    product_tracking = fields.Selection(string="sel", related="product_id.tracking")
    lot_id_domain = fields.Char(
        compute="_compute_lot_domain",
        readonly=True,
        store=False,
    )

    @api.onchange('lot_id')
    def change_calibration_date(self):
        for rec in self:
            if rec.lot_id:
                rec.calibration_date = rec.lot_id.calibration_date
                if rec.lot_id.note:
                    rec.lot_description = rec.lot_id.note.replace("<p>", "").replace("</p>", "")
                else:
                    rec.lot_description = rec.lot_id.note
                rec.lot_ref = rec.lot_id.ref
            else:
                rec.calibration_date = False
                rec.lot_description = False
                rec.lot_ref = False
            if rec.lot_description:
                rec.lot_description.replace("<p>", "").replace("</p>", "")

    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_to_delete = OrderedSet()
        lot_vals_to_create = []  # lot values for batching the creation
        associate_line_lot = []  # move_line to associate to the lot
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision '
                                  'defined on the unit of measure "%s". Please change the quantity done or the '
                                  'rounding precision of your unit of measure.') % (
                                ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot_vals_to_create.append(
                                    {
                                        'name': ml.lot_name,
                                        'product_id': ml.product_id.id,
                                        'ref': ml.lot_ref,
                                        'note': ml.lot_description,
                                        'calibration_date': ml.calibration_date,
                                        'company_id': ml.move_id.company_id.id
                                    })
                                associate_line_lot.append(ml)
                                continue  # Avoid the raise after because not lot_id is set
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_ids_to_delete.add(ml.id)

        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()

        # Batching the creation of lots and associated each to the right ML (order is preserve in the create)
        lots = self.env['stock.production.lot'].create(lot_vals_to_create)
        for ml, lot in zip(associate_line_lot, lots):
            ml.write({'lot_id': lot.id})

        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()

        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        for ml in mls_todo:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty,
                                                                                       precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id,
                                                                               rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id,
                                         owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
                # unreserve what's been reserved
                if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id,
                                                    package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                               rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                          lot_id=ml.lot_id, package_id=ml.package_id,
                                                                          owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                  package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False,
                                                         package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                         lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                 package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            ml_ids_to_ignore.add(ml.id)
        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `qty_done` to 1.0
            - warn if he has already encoded `lot_name` in another move line
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if not self.qty_done:
                self.qty_done = 1
            if not self.lot_description and self.move_id.description_picking:
                self.lot_description = self.move_id.description_picking.replace("<p>", "").replace("</p>", "")
            if self.lot_description and self.lot_description:
                self.lot_description = self.lot_description.replace("<p>", "").replace("</p>", "")

            message = None
            if self.lot_name or self.lot_id:
                move_lines_to_check = self._get_similar_move_lines() - self
                if self.lot_name:
                    counter = Counter([line.lot_name for line in move_lines_to_check])
                    if counter.get(self.lot_name) and counter[self.lot_name] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                elif self.lot_id:
                    counter = Counter([line.lot_id.id for line in move_lines_to_check])
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')

            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    def write(self, vals):
        res = True
        if self.env.context.get('bypass_reservation_update'):
            return super(StockMoveLine, self).write(vals)

        if 'product_id' in vals and any(
                vals.get('state', ml.state) != 'draft' and vals['product_id'] != ml.product_id.id for ml in self):
            raise UserError(_("Changing the product is only allowed in 'Draft' state."))

        moves_to_recompute_state = self.env['stock.move']
        Quant = self.env['stock.quant']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.production.lot'),
            ('package_id', 'stock.quant.package'),
            ('result_package_id', 'stock.quant.package'),
            ('owner_id', 'res.partner'),
            ('product_uom_id', 'uom.uom')
        ]
        updates = {}
        for key, model in triggers:
            if key in vals:
                updates[key] = self.env[model].browse(vals[key])

        if 'result_package_id' in updates:
            for ml in self.filtered(lambda ml: ml.package_level_id):
                if updates.get('result_package_id'):
                    ml.package_level_id.package_id = updates.get('result_package_id')
                else:
                    # TODO: make package levels less of a pain and fix this
                    package_level = ml.package_level_id
                    ml.package_level_id = False
                    package_level.unlink()

        # When we try to write on a reserved move line any fields from `triggers` or directly
        # `product_uom_qty` (the actual reserved quantity), we need to make sure the associated
        # quants are correctly updated in order to not make them out of sync (i.e. the sum of the
        # move lines `product_uom_qty` should always be equal to the sum of `reserved_quantity` on
        # the quants). If the new charateristics are not available on the quants, we chose to
        # reserve the maximum possible.
        if updates or 'product_uom_qty' in vals:
            for ml in self.filtered(
                    lambda ml: ml.state in ['partially_available', 'assigned'] and ml.product_id.type == 'product'):

                if 'product_uom_qty' in vals:
                    new_product_uom_qty = ml.product_uom_id._compute_quantity(
                        vals['product_uom_qty'], ml.product_id.uom_id, rounding_method='HALF-UP')
                    # Make sure `product_uom_qty` is not negative.
                    if float_compare(new_product_uom_qty, 0, precision_rounding=ml.product_id.uom_id.rounding) < 0:
                        raise UserError(_('Reserving a negative quantity is not allowed.'))
                else:
                    new_product_uom_qty = ml.product_qty

                # Unreserve the old charateristics of the move line.
                if not ml._should_bypass_reservation(ml.location_id):
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id,
                                                    package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # Reserve the maximum available of the new charateristics of the move line.
                if not ml._should_bypass_reservation(updates.get('location_id', ml.location_id)):
                    reserved_qty = 0
                    try:
                        q = Quant._update_reserved_quantity(ml.product_id, updates.get('location_id', ml.location_id),
                                                            new_product_uom_qty, lot_id=updates.get('lot_id', ml.lot_id),
                                                            package_id=updates.get('package_id', ml.package_id),
                                                            owner_id=updates.get('owner_id', ml.owner_id), strict=True)
                        reserved_qty = sum([x[1] for x in q])
                    except UserError:
                        pass
                    if reserved_qty != new_product_uom_qty:
                        new_product_uom_qty = ml.product_id.uom_id._compute_quantity(reserved_qty, ml.product_uom_id,
                                                                                     rounding_method='HALF-UP')
                        moves_to_recompute_state |= ml.move_id
                        ml.with_context(bypass_reservation_update=True).product_uom_qty = new_product_uom_qty

        # When editing a done move line, the reserved availability of a potential chained move is impacted. Take care of running again `_action_assign` on the concerned moves.
        next_moves = self.env['stock.move']
        if updates or 'qty_done' in vals:
            mls = self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.type == 'product')
            if not updates:  # we can skip those where qty_done is already good up to UoM rounding
                mls = mls.filtered(
                    lambda ml: not float_is_zero(ml.qty_done - vals['qty_done'], precision_rounding=ml.product_uom_id.rounding))
            for ml in mls:
                # undo the original move line
                qty_done_orig = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                                    rounding_method='HALF-UP')
                in_date = Quant._update_available_quantity(ml.product_id, ml.location_dest_id, -qty_done_orig, lot_id=ml.lot_id,
                                                           package_id=ml.result_package_id, owner_id=ml.owner_id)[1]
                Quant._update_available_quantity(ml.product_id, ml.location_id, qty_done_orig, lot_id=ml.lot_id,
                                                 package_id=ml.package_id, owner_id=ml.owner_id, in_date=in_date)

                # move what's been actually done
                product_id = ml.product_id
                location_id = updates.get('location_id', ml.location_id)
                location_dest_id = updates.get('location_dest_id', ml.location_dest_id)
                qty_done = vals.get('qty_done', ml.qty_done)
                lot_id = updates.get('lot_id', ml.lot_id)
                package_id = updates.get('package_id', ml.package_id)
                result_package_id = updates.get('result_package_id', ml.result_package_id)
                owner_id = updates.get('owner_id', ml.owner_id)
                product_uom_id = updates.get('product_uom_id', ml.product_uom_id)
                quantity = product_uom_id._compute_quantity(qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                if not ml._should_bypass_reservation(location_id):
                    ml._free_reservation(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id,
                                         owner_id=owner_id)
                if not float_is_zero(quantity, precision_digits=precision):
                    available_qty, in_date = Quant._update_available_quantity(product_id, location_id, -quantity, lot_id=lot_id,
                                                                              package_id=package_id, owner_id=owner_id)
                    if available_qty < 0 and lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(product_id, location_id, lot_id=False,
                                                                      package_id=package_id, owner_id=owner_id, strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(available_qty))
                            Quant._update_available_quantity(product_id, location_id, -taken_from_untracked_qty, lot_id=False,
                                                             package_id=package_id, owner_id=owner_id)
                            Quant._update_available_quantity(product_id, location_id, taken_from_untracked_qty, lot_id=lot_id,
                                                             package_id=package_id, owner_id=owner_id)
                            if not ml._should_bypass_reservation(location_id):
                                ml._free_reservation(ml.product_id, location_id, untracked_qty, lot_id=False,
                                                     package_id=package_id, owner_id=owner_id)
                    Quant._update_available_quantity(product_id, location_dest_id, quantity, lot_id=lot_id,
                                                     package_id=result_package_id, owner_id=owner_id, in_date=in_date)

                # Unreserve and reserve following move in order to have the real reserved quantity on move_line.
                next_moves |= ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))

                # Log a note
                if ml.picking_id:
                    ml._log_message(ml.picking_id, ml, 'stock.track_move_template', vals)

        if 'lot_id' in vals and vals['lot_id'] != False:
            res = super(StockMoveLine, self).write(vals)

        # Update scrap object linked to move_lines to the new quantity.
        if 'qty_done' in vals:
            for move in self.mapped('move_id'):
                if move.scrapped:
                    move.scrap_ids.write({'scrap_qty': move.quantity_done})

        # As stock_account values according to a move's `product_uom_qty`, we consider that any
        # done stock move should have its `quantity_done` equals to its `product_uom_qty`, and
        # this is what move's `action_done` will do. So, we replicate the behavior here.
        if updates or 'qty_done' in vals:
            moves = self.filtered(lambda ml: ml.move_id.state == 'done').mapped('move_id')
            moves |= self.filtered(lambda ml: ml.move_id.state not in (
            'done', 'cancel') and ml.move_id.picking_id.immediate_transfer and not ml.product_uom_qty).mapped('move_id')
            for move in moves:
                move.product_uom_qty = move.quantity_done
        next_moves._do_unreserve()
        next_moves._action_assign()

        if moves_to_recompute_state:
            moves_to_recompute_state._recompute_state()

        return res