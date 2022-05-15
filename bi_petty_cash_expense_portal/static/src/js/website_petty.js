odoo.define('bi_petty_cash_expense_portal.website_petty', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var concurrency = require('web.concurrency');
var publicWidget = require('web.public.widget');
require("web.zoomodoo");

var qweb = core.qweb;

publicWidget.registry.WebsitePetty = publicWidget.Widget.extend({
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
            route: '/petty/petty_company_infos',
            params: {
                company: $("#company_id").val(),
                currency: $("#petty_currency_id").val(),
                employee: $("#petty_employee_id").val(),
            },
        }).then(function (data) {
            // populate products and display
            var selectProducts = $("select[name='product_id']");
            // dont reload task at first loading (done in qweb)
            if (selectProducts.data('init')===0 || selectProducts.find('option').length===1) {
                if (data.products.length) {
                    selectProducts.html('');
                    _.each(data.products, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectProducts.append(opt);
                    });
                } else {
                      selectProducts.empty();
                }
                selectProducts.data('init', 0);
            } else {
                selectProducts.data('init', 0);
            }

            // accounts
            var selectAccounts = $("select[name='account_id']");
            if (selectAccounts.data('init')===0 || selectAccounts.find('option').length===1) {
                if (data.accounts.length) {
                    selectAccounts.html('');
                    _.each(data.accounts, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectAccounts.append(opt);
                    });
                } else {
                      selectAccounts.empty();
                }
                selectAccounts.data('init', 0);
            } else {
                selectAccounts.data('init', 0);
            }

            // analytic
            var selectAnalyticAccounts = $("select[name='analytic_account_id']");
            if (selectAnalyticAccounts.data('init')===0 || selectAnalyticAccounts.find('option').length===1) {
                if (data.analytic_accounts.length) {
                    selectAnalyticAccounts.html('');
                    _.each(data.analytic_accounts, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectAnalyticAccounts.append(opt);
                    });
                } else {
                      selectAnalyticAccounts.empty();
                }
                selectAnalyticAccounts.data('init', 0);
            } else {
                selectAnalyticAccounts.data('init', 0);
            }

            var selectAnalyticTags = $("select[name='analytic_tag_id']");
            if (selectAnalyticTags.data('init')===0 || selectAnalyticTags.find('option').length===1) {
                if (data.analytic_tags.length) {
                    selectAnalyticTags.html('');
                    _.each(data.analytic_tags, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectAnalyticTags.append(opt);
                    });
                } else {
                      selectAnalyticTags.empty();
                }
                selectAnalyticTags.data('init', 0);
            } else {
                selectAnalyticTags.data('init', 0);
            }

        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeCompany: function (ev) {
        if (!this.$('.petty_company_auto').length) {
            return;
        }
        this._changeCompany();
    },
});
});