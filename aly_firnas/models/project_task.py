# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProjectTaskPredecessor(models.Model):
    _inherit = 'project.task.predecessor'
    _description = 'project.task.predecessor'


class ProjectTaskDetailPlan(models.Model):
    _inherit = 'project.task.detail.plan'
    _description = 'project.task.detail.plan'


class ProjectTaskDetailInfo(models.Model):
    _inherit = 'project.task.info'
    _description = 'project.task.info'


class ProjectTaskDetailInfo21(models.Model):
    _inherit = 'project.task.resource.link'
    _description = 'project.task.resource.link'


class ProjectTaskDetailInfo2(models.Model):
    _inherit = 'project.native.exchange.tool'
    _description = 'project.native.exchange.tool'


class ProjectTaskDetailInfo3(models.Model):
    _inherit = 'project.native.exchange.import.task.line'
    _description = 'project.native.exchange.import.task.line'


class ProjectTaskDetailInfo22(models.Model):
    _inherit = 'project.native.exchange.import.prj.line'
    _description = 'project.native.exchange.import.prj.line'


class ProjectTaskDetailInfo24(models.Model):
    _inherit = 'project.native.exchange.import'
    _description = 'project.native.exchange.import'


class ProjectTaskDetailInfo25(models.Model):
    _inherit = 'project.native.exchange'
    _description = 'project.native.exchange'


class ProjectTaskDetailInfo15(models.Model):
    _inherit = 'report.project_native_report.project_native_gantt_report'
    _description = 'report.project_native_report.project_native_gantt_report'


class ProjectTaskDetailInfo16(models.Model):
    _inherit = 'project.native.report'
    _description = 'project.native.report'


class ProjectTaskDetailInfo17(models.Model):
    _inherit = 'purchase.lines.transfer.wizard'
    _description = 'purchase.lines.transfer.wizard'


class ProjectTaskDetailInfo18(models.Model):
    _inherit = 'purchase.line.wizard'
    _description = 'purchase.line.wizard'


class ProjectTaskDetailInfo18(models.Model):
    _inherit = 'purchase.line.wizard'
    _description = 'purchase.line.wizard'


class ProjectTaskDetailInfo19(models.Model):
    _inherit = 'project.submission'
    _description = 'project.submission'


class ProjectTaskDetailInfo100(models.Model):
    _inherit = 'project.fund'
    _description = 'project.fund'


class ProjectTaskDetailInfo101(models.Model):
    _inherit = 'project.partnership'
    _description = 'project.partnership'


class ProjectTaskDetailInfo102(models.Model):
    _inherit = 'project.source'
    _description = 'project.source'


class ProjectTaskDetailInfo103(models.Model):
    _inherit = 'expected.revenue'
    _description = 'expected.revenue'
