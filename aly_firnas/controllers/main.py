# -*- coding: utf-8 -*-

from odoo import http, _, fields
from odoo.http import request
from datetime import datetime


class WHPortal(http.Controller):

    @http.route('/my/wh_hello/', auth="user", website=True)
    def portal_wh_hello(self, **kw):
        return "Hello"

    @http.route('/my/wh_confirmation_accept/<int:wh_id>', auth="user", website=True)
    def portal_wh_accept(self, wh_id, **kw):
        response = super(WHPortal, self)
        if wh_id:
            wh_sudo = request.env['stock.picking'].sudo().browse(wh_id)

            employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            x = datetime.now()
            if wh_sudo and employee:
                body = "WH has been <strong>Approved</strong> on <strong>{}</strong> by {}".format(x.strftime("%d-%b-%Y %I:%M %p"), employee.name)
                wh_sudo.message_post(body=body)
        return request.render("aly_issue_request.thankyou_page")

    @http.route(['/my/wh_confirmation_reject/<int:wh_id>'], type='http', auth="user", website=True)
    def portal_wh_reject(self, wh_id, report_type=None, access_token=None, message=False, download=False, **kw):
        response = super(WHPortal, self)
        if wh_id:
            wh_sudo = request.env['stock.picking'].sudo().browse(wh_id)

            employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            x = datetime.now()
            if wh_sudo and employee:
                body = "WH has been <strong>Rejected</strong> on <strong>{}</strong> by {}".format(x.strftime("%d-%b-%Y %I:%M %p"), employee.name)
                wh_sudo.message_post(body=body)
        return request.render("aly_issue_request.thankyou_page_reject")
