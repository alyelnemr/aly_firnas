# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectProjectInherit(models.Model):
    _inherit = 'project.project'

    project_num = fields.Char(string="Project Number")
    type = fields.Integer(string="Type")
    country = fields.Many2many('res.country', string='Country')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    source = fields.Many2one('project.source', string="Source")
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner = fields.Many2many('res.partner', string="Partner")
    partner_id = fields.Many2one('res.partner', string='Customer')
    # client_name = fields.Many2many('client.name', string="Client")

