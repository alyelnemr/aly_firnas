odoo.define('bi_bundle.delete', function (require) {
    "use strict";
    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _onRemoveIconClick: function (event) {
            var self = this;
            this._super(event);
        
            if (this.state.model === "sale.order.line") {
                var $row = $(event.target).closest('tr');
                var id = $row.data('id');
                //  loop all rec to get dic of id and res_id
                var view_ids = {}
                var ids={}
                this.state.data.forEach(element => {
                    view_ids[element.id] = element.res_id
                    ids[element.res_id] = element.id
                });
                this._rpc({
                    model: "sale.order.line",
                    method: "get_sub_products",
                    args: ["", view_ids[id],ids],
                }).then(function (subs) {
                    subs.forEach(sub => {
                        self.trigger_up('list_record_remove', { id: sub })
                    });
                   


                })
            }

        }
    });



});
