# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectFunding(models.Model):
    _name = 'project.fund'

    name = fields.Char('name')
