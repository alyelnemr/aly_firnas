import base64
import uuid
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
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', domain=_compute_lot_domain, check_company=True)
    attachment_document = fields.Binary(string='Attachment', required=False)

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
        if ml.attachment_document:
            IrAttachment = self.env['ir.attachment']
            IrAttachment = IrAttachment.sudo().with_context(binary_field_real_user=self.env.user)
            access_token = IrAttachment._generate_access_token()
            file_name = ml.attachment_document.filename or lots.name + '_' + str(uuid.uuid4())
            attachment_id = IrAttachment.create({
                'name': file_name,
                'datas': base64.b64encode(ml.attachment_document.read()),
                'res_model': 'mail.compose.message',
                'res_id': 0,
                'access_token': access_token,
            })
            lots.message_post(attachment_ids=[attachment_id.id])
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
