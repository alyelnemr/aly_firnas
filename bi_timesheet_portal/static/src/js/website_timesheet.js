odoo.define('bi_timesheet_portal.website_timesheet', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var concurrency = require('web.concurrency');
var publicWidget = require('web.public.widget');
require("web.zoomodoo");

var qweb = core.qweb;

publicWidget.registry.WebsiteTimesheet = publicWidget.Widget.extend({
    selector: '.o_portal_wrap',
    events:{
        'change select[name="company_id"]': '_onChangeCompany',
        'change select[name="project_id"]': '_onChangeProject',
    },

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this._changeCompany = _.debounce(this._changeCompany.bind(this), 500);
        this._changeProject = _.debounce(this._changeProject.bind(this), 500);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        this.$('select[name="company_id"]').change();
        this.$('select[name="project_id"]').change();
        return def;
    },

    /**
     * @private
     */
    _changeProject: function () {
//        if (!$("#project_id").val()) {
//            return;
//        }
        this._rpc({
            route: "/timesheet/project_infos/",
            params: {
                project: $("#project_id").val(),
            },
        }).then(function (data) {
            // populate tasks and display
            var selectTasks = $("select[name='task_id']");
            // dont reload task at first loading (done in qweb)
            if (selectTasks.data('init')===0 || selectTasks.find('option').length===1) {
                if (data.tasks.length) {
                    selectTasks.html('');
                    _.each(data.tasks, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectTasks.append(opt);
                    });
//                    selectTasks.parent('div').show();
                } else {
//                    selectTasks.val('').parent('div').hide();
                      selectTasks.empty();
                }
                selectTasks.data('init', 0);
            } else {
                selectTasks.data('init', 0);
            }
        });
    },

    _changeCompany: function () {
        this._rpc({
            route: "/timesheet/company_info/",
            params: {
                company: $("#company_id").val(),
            },
        }).then(function (data) {
            // populate projects and display
            var selectProjects = $("select[name='project_id']");
            var selectTasks = $("select[name='task_id']");
            // dont reload task at first loading (done in qweb)
            if (selectProjects.data('init')===0 || selectProjects.find('option').length===1) {
                if (data.projects.length) {
                    selectProjects.html('');
                    _.each(data.projects, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectProjects.append(opt);
                    });
                } else {
                      selectProjects.empty();
                }
                selectProjects.data('init', 0);
            } else {
                selectProjects.data('init', 0);
            }
        });
        this._changeProject();
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeProject: function (ev) {
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        this._changeProject();
    },
    _onChangeCompany: function (ev) {
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        this._changeCompany();
    },
});
});