odoo.define('bi_expense_portal.website_expense', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var concurrency = require('web.concurrency');
var publicWidget = require('web.public.widget');
require("web.zoomodoo");

var qweb = core.qweb;

publicWidget.registry.WebsiteExpense = publicWidget.Widget.extend({
    selector: '.o_portal_wrap',
    events:{
        'change select[name="company_id"]': '_onChangeCompany',
        'change select[name="partner_id"]': '_onChangeVendor',
        'change select[name="project_id"]': '_onChangeProject',
        'change select[name="product_id"]': '_onChangeProduct',
    },

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this._changeCompany = _.debounce(this._changeCompany.bind(this), 500);
        this._changeVendor = _.debounce(this._changeVendor.bind(this), 500);
        this._changeProject = _.debounce(this._changeProject.bind(this), 500);
        this._changeProduct = _.debounce(this._changeProduct.bind(this), 500);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        this.$('select[name="company_id"]').change();
        this.$('select[name="partner_id"]').change();
        this.$('select[name="project_id"]').change();
        return def;
    },

    /**
     * @private
     */
    _changeCompany: function () {
        this._rpc({
            route: '/expense/company_infos',
            params: {
                company: $("#company_id").val(),
                product: $("#product_id").val(),
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
        });
    },
    _changeVendor: function () {
        this._rpc({
            route: '/expense/vendor_contacts',
            params: {
                vendor: $("#partner_id").val(),
            },
        }).then(function (data) {
            // populate products and display
            var selectVendorContacts = $("select[name='vendor_contact']");

            // dont reload task at first loading (done in qweb)
            if (selectVendorContacts.data('init')===0 || selectVendorContacts.find('option').length===1) {
                if (data.vendor_contacts.length) {
                    selectVendorContacts.html('');
                    _.each(data.vendor_contacts, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]);
                        selectVendorContacts.append(opt);
                    });
                } else {
                    selectVendorContacts.empty();
                }
                selectVendorContacts.data('init', 0);
            } else {
                selectVendorContacts.data('init', 0);
            }
        });
    },
    _changeProject: function () {
        this._rpc({
            route: '/expense/project_change',
            params: {
                project_id_str: $("#project_id").val(),
            },
        }).then(function (data) {

            $("#company_id").val(data.company_data);

            var selectAnalyticAccounts = $("select[name='analytic_account_id']");
            if (selectAnalyticAccounts.data('init')===0 || selectAnalyticAccounts.find('option').length===1) {
                if (data.analytic_account_data.length) {
                    selectAnalyticAccounts.html('');
                    _.each(data.analytic_account_data, function (x) {
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
                if (data.analytic_tags_data.length) {
                    selectAnalyticTags.html('');
                    _.each(data.analytic_tags_data, function (x) {
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
    _changeProduct: function () {
        this._rpc({
            route: '/expense/product_change',
            params: {
                product_id_str: $("#product_id").val(),
            },
        }).then(function (data) {

            // populate products and display
            var selectProducts = $("select[name='account_id']");

            // dont reload task at first loading (done in qweb)
            if (selectProducts.data('init')===0 || selectProducts.find('option').length===1) {
                if (data.default_account.length) {
                    selectProducts.html('');
                    _.each(data.default_account, function (x) {
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
        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeCompany: function (ev) {
        if (!this.$('.company_autoformat').length) {
            return;
        }
        this._changeCompany();
    },
    _onChangeVendor: function (ev) {
        if (!this.$('select[name="partner_id"]').length) {
            return;
        }
        this._changeVendor();
    },
    _onChangeProject: function (ev) {
        if (!this.$('select[name="project_id"]').length) {
            return;
        }
        this._changeProject();
    },
    _onChangeProduct: function (ev) {
        if (!this.$('select[name="product_id"]').length) {
            return;
        }
        this._changeProduct();
    },
});
});