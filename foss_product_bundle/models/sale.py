# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    seq = fields.Integer(string='Sequence')
    child_line = fields.One2many('child.product.line', 'product_tmp_id', string='Products')

    def write(self, vals):
        if self.child_line:
            for line in self.child_line:
                line.product_id.seq = 10
        if self.type == 'service':
            vals.update({
                'seq': 1
            })
        return super(ProductTemplate, self).write(vals)


class ChildProductLine(models.Model):
    _name = "child.product.line"

    product_tmp_id = fields.Many2one('product.template', string='Product Name')
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity')
    seq = fields.Integer(string='Sequence')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_offer_product = fields.Boolean(string='Seq', readonly=True)
    parent_order_line = fields.Many2one('sale.order.line', string="Parent Line")
    bundle_status = fields.Char(
        'Bundle_status', compute='line_bundle_status')
    is_update = fields.Boolean(string="Show Update button", compute="_compute_is_update")

    @api.depends('bundle_status', 'order_id.order_line', 'product_id')
    def _compute_is_update(self):
        for line in self:
            if line.is_bundle(line):
                line.is_update = True
            else:
                line.is_update = False

    def action_unlink(self):
        for line in self:
            related_lines = line.order_id.order_line.search([('parent_order_line','=', line.id)])
            # get child bundles 
            related_lines+=line.order_id.order_line.search([('parent_order_line','in', related_lines.ids)])
            if related_lines:
                related_lines.unlink()
            line.unlink()

    def get_sub_products(self,line_id,view_ids):
       
        line=self.search([('id','=',line_id)])
        related_lines = line.order_id.order_line.search([('parent_order_line','=', line.id)])
        related_lines+=line.order_id.order_line.search([('parent_order_line','in', related_lines.ids)])
        
        return [view_ids[str(id)]for id in related_lines.ids]
         

    @api.model
    def create(self, vals):
        seq = 1000
        if vals.get('order_id') and not vals.get('is_offer_product'):
            self._cr.execute("""select max(sequence) from sale_order_line where order_id = %s""",
                             (vals.get('order_id'),))
            res = self._cr.fetchone()
            if res and res[0]:
                if res[0] % 100 != 0:
                    rem = res[0] % 1000
                    vals['sequence'] = (res[0] - rem) + 1000
                else:
                    vals['sequence'] = res[0] + 1000
            else:
                vals['sequence'] = seq
        return super(SaleOrderLine, self).create(vals)

    def _prepare_invoice_line(self):
        res = {}
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        if res:
            res.update({'is_offer_product': self.is_offer_product})
        return res

    def update_product(self):
        ''' Create offer products against the selling product. '''
        # +1 for order sub-products after bundle seq
        
        for line in self:
            vals_tools = []
            ext_line = [x.product_id.id for x in line.order_id.order_line if x.parent_order_line == line.id]
            line_seq=0    
            if line.product_id.child_line:  
                for ch_line in line.product_id.child_line:
                    line_seq+=1
                    if line.is_offer_product:
                        if ch_line.product_id.id not in ext_line:
                            if line.product_uom_qty > 0 and ch_line.product_qty > 0:
                                vals_tools.append((0, 2, {
                                    'sequence': line.sequence+line_seq,
                                    'section':line.section.id,
                                    'product_id': ch_line.product_id.id,
                                    'parent_order_line': line.id,
                                    'product_uom_qty': line.product_uom_qty * ch_line.product_qty,
                                    'analytic_tag_ids':line.analytic_tag_ids.ids,
                                    'is_offer_product': True
                                }))
                                line_seq+=50 if ch_line.product_id.child_line.ids else 0 
                            else:
                                raise UserError(('Product Qty Should be greater than Zero.'))
                    else:
                        products_generated = [x.product_id.id for x in line.order_id.order_line.filtered(
                            lambda l: l.parent_order_line and l.parent_order_line.id == line.id)]
                        if ch_line.product_id.id not in products_generated:
                            if line.product_uom_qty > 0 and ch_line.product_qty > 0:
                                vals_tools.append((0, 2, {
                                    'sequence': line.sequence+line_seq,
                                    'section':line.section.id,
                                    'product_id': ch_line.product_id.id,
                                    'parent_order_line': line.id,
                                    'product_uom_qty': line.product_uom_qty * ch_line.product_qty,
                                    'analytic_tag_ids':line.analytic_tag_ids.ids,
                                    'is_offer_product': True
                                }))
                                line_seq+=50 if ch_line.product_id.child_line.ids else 0 
                            else:
                                raise UserError(('Product Qty Should be greater than Zero.'))
            line.order_id.order_line = vals_tools
        return True

    @api.onchange('section')
    def update_bundle_lines_section(self):
        for line in self:
            if line.ids:
                related_lines = line.order_id.order_line.search(
                    [('parent_order_line', '=', line.ids[0])])
                line.update_sections(line,related_lines)
               



    def update_sections(self,line,related_lines):
        if not related_lines:
            return 
        else:
            for related_line in related_lines:
                related_lines = related_line.order_id.order_line.search(
                    [('parent_order_line', '=', related_line.ids[0])])
                related_line.section=line.section
                if related_lines:
                    related_line.update_sections(related_line,related_lines)   
                

    #check line is bundle or not or bundle form bundle 
    
    def line_bundle_status(self):
        for line in self:
            if line.is_bundle(line):
                if line.is_bundel_of_bundle(line):
                    line.bundle_status = 'bundel_of_bundle'
                    return 'bundel_of_bundle'
                line.bundle_status = 'bundle'
                return 'bundle'
            line.bundle_status = 'not_bundle'
            return 'not_bundle'

    def is_bundle(self,line):
        related_lines = self.order_id.order_line.search(
            [('parent_order_line', '=', line.id)])
        return related_lines.ids

    def is_bundel_of_bundle(self, line_id):
        for line in self.order_id.order_line:
            related_lines = self.order_id.order_line.search(
                [('parent_order_line', '=', line.ids[0])])
            if line_id.id in related_lines.ids:
                return related_lines
        return False
class StockMove(models.Model):
    _inherit = 'stock.move'

    is_offer_product = fields.Boolean(string='Is Offer Product', readonly=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_offer_product = fields.Boolean(string='Is Offer Product', readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
