# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectSubmission(models.Model):
    _name = 'project.submission'
    _description = 'project.submission'

    name = fields.Char('name')
