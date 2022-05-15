# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectSource(models.Model):
    _name = 'project.source'

    name = fields.Char('name')
