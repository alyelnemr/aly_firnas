# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields):
        vals = super(ProductProduct, self).default_get(fields)
        vals['state'] = 'draft'
        return vals

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')], default='draft', string='Status', copy=False)
    is_downpayment_service = fields.Boolean('Is Downpayment Service', default=False)
    # default_code = fields.Char(
    #     'Internal Reference', compute='_compute_default_code',
    #     inverse='_set_default_code', store=True, copy=True)
    # description_sale = fields.Text(
    #     'Sales Description', translate=True, copy=False,
    #     help="A description of the Product that you want to communicate to your customers. "
    #          "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'default_code' not in default:
            old_code = self.env['product.template'].search([('default_code', '=', self.default_code)])
            new_code = ''
            if old_code:
                new_code = self.default_code + '_' + str(len(old_code))
            default['default_code'] = new_code
        if 'description_sale' not in default:
            default['description_sale'] = False
        if 'description' not in default:
            default['description'] = False
        if 'description_pickingout' not in default:
            default['description_pickingout'] = False
        if 'description_pickingin' not in default:
            default['description_pickingin'] = False
        if 'description_picking' not in default:
            default['description_picking'] = False
        if 'description_purchase' not in default:
            default['description_purchase'] = False
        return super(ProductProduct, self).copy(default=default)

    def write(self, vals):
        if 'state' in vals:
            has_my_group = self.env.user.has_group('aly_firnas.group_update_product_state')
            if not has_my_group:
                raise ValidationError("Sorry you can't edit state for products!")
        if 'default_code' in vals:
            new_code = vals['default_code']
            old_code = self.env['product.template'].search([('default_code', '=', new_code)])
            if old_code:
                raise ValidationError("Internal Reference can only be assigned to one product .")
        res = super(ProductProduct, self).write(vals)
        return res

    def action_state_approve(self):
        self.state = 'draft' if self.state == 'approved' else 'approved'
