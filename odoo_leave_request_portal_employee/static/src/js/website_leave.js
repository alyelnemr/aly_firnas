odoo.define('odoo_leave_request_portal_employee.website_leave', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var concurrency = require('web.concurrency');
var publicWidget = require('web.public.widget');
require("web.zoomodoo");

var qweb = core.qweb;

publicWidget.registry.WebsiteLeave = publicWidget.Widget.extend({
    selector: '.o_portal_wrap',
    events:{
        'change select[name="company_id"]': '_onChangeCompany',
    },

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this._changeCompany = _.debounce(this._changeCompany.bind(this), 500);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        this.$('select[name="company_id"]').change();
        return def;
    },

    /**
     * @private
     */
    _changeCompany: function () {
        this._rpc({
            route: '/leave/leave_company_infos',
            params: {
                company: $("#company_id").val(),
            },
        }).then(function (data) {
            // populate leave_types and display
            var selectLeaveTypeype = $("select[name='leave_type']");
            if (selectLeaveTypeype.data('init')===0 || selectLeaveTypeype.find('option').length===1) {
                if (data.leave_types.length) {
                    selectLeaveTypeype.html('');
                    _.each(data.leave_types, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectLeaveTypeype.append(opt);
                    });
                } else {
                      selectLeaveTypeype.empty();
                }
                selectLeaveTypeype.data('init', 0);
            } else {
                selectLeaveTypeype.data('init', 0);
            }
        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeCompany: function (ev) {
        if (!this.$('.container-fluid').length) {
            return;
        }
        this._changeCompany();
    },
});
});