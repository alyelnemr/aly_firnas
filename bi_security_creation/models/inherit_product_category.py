# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    @api.model
    def create(self, vals):
        has_my_group = self.env.user.has_group('bi_security_creation.group_create_product_category')
        if not has_my_group:
            raise exceptions.ValidationError("Sorry you can't create product categories!")
        return super(ProductCategoryInherit, self).create(vals)


    
    def write(self, vals):
        has_my_group = self.env.user.has_group('bi_security_creation.group_create_product_category')
        if not has_my_group:
            raise exceptions.ValidationError("Sorry you can't edit product categories!")
        return super(ProductCategoryInherit, self).write(vals)
