# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CRMLeadInherit(models.Model):
    _inherit = 'crm.lead'

    name = fields.Char('Opportunity', default='/', index=True, compute='_compute_name', store=True)
    is_existing_opportunity = fields.Boolean(string='Is it an existing opportunity?')
    parent_opportunity_id = fields.Many2one('crm.lead', string='Existing Opportunities')
    serial_number = fields.Char(string='Serial Number')
    original_serial_number = fields.Char(string='Original Serial Number')
    type_custom = fields.Many2one('crm.type', string="Type", required=True)
    letter_identifier = fields.Char(string='Letter Identifier')
    project_num = fields.Char(string="Project Number", default='/', compute='_compute_project_num', store=True)
    internal_opportunity_name = fields.Char(string="Internal Opportunity Name", required=True)
    next_letter_sequence = fields.Char(string="Next Letter Sequence", readonly=True)

    @api.depends('project_num', 'country.code', 'internal_opportunity_name')
    def _compute_name(self):
        for record in self:
            if record.project_num and record.country and record.internal_opportunity_name:
                countries_code = "-".join(record.country.mapped('code'))
                record.name = record.project_num + ' -' + countries_code + '- ' + record.internal_opportunity_name
            else:
                record.name = '/'

    @api.depends('serial_number', 'type_custom.type_no', 'letter_identifier')
    def _compute_project_num(self):
        for record in self:
            if record.type_custom:
                if record.letter_identifier:
                    record.project_num = (record.serial_number or '') + record.type_custom.type_no + record.letter_identifier
                else:
                    record.project_num = (record.serial_number or '') + record.type_custom.type_no
            else:
                record.project_num = '/'

    @api.model
    def create(self, vals):
        if vals.get('type') == 'opportunity' or self._context.get('default_type') == 'opportunity':
            if not vals.get('serial_number'):
                if vals.get('is_existing_opportunity'):
                    parent_opp = self.env['crm.lead'].browse(vals['parent_opportunity_id'])
                    vals['serial_number'] = parent_opp.serial_number

                    # parent opportunity next letter sequence
                    if vals.get('letter_identifier'):
                        next_letter_sequence = chr(ord(vals.get('letter_identifier')) + 1)
                        parent_opp.sudo().write({'next_letter_sequence': next_letter_sequence})
                else:
                    new_serial_no = self.env['ir.sequence'].next_by_code('bi_crm_concatenated_name.serial_no') or _(
                        'New')
                    vals['serial_number'] = new_serial_no

            vals['original_serial_number'] = vals['serial_number']

        res = super(CRMLeadInherit, self).create(vals)
        return res

    def write(self, vals):
        if 'parent_opportunity_id' in vals:
            if self.type == 'opportunity':
                if vals['parent_opportunity_id']:
                    parent_opp = self.env['crm.lead'].browse(vals['parent_opportunity_id'])
                    vals['serial_number'] = parent_opp.serial_number
                else:
                    vals['serial_number'] = self.original_serial_number

        return super(CRMLeadInherit, self).write(vals)

    def action_new_quotation(self):
        res = super(CRMLeadInherit, self).action_new_quotation()
        res['context']['default_type_custom'] = self.type_custom.name
        return res

    @api.onchange('is_existing_opportunity')
    def reset_parent_opportunity_id(self):
        if not self.is_existing_opportunity:
            self.parent_opportunity_id = False

    @api.onchange('parent_opportunity_id')
    def get_related_country(self):
        for rec in self:
            if rec.parent_opportunity_id and rec.parent_opportunity_id.country:
                rec.country = rec.parent_opportunity_id.country
            else:
                rec.country = False

            # parent opprtunity letter sequence
            if rec.parent_opportunity_id:
                rec.letter_identifier = rec.parent_opportunity_id.next_letter_sequence or 'B'
            else:
                rec.letter_identifier = False
