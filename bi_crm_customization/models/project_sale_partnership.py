# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectPartnership(models.Model):
    _name = 'project.partnership'
    _description = 'project.partnership'

    name = fields.Char('name')
