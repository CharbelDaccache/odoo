odoo.define('partner_number.custom_form_widget', function (require) {
"use strict";

var core = require('web.core');
var FieldChar = core.form_widget_registry.get('char');
var _t = core._t;
var QWeb = core.qweb;

var CustomFieldUrl = FieldChar.extend({
    template: 'CustomFieldUrl',

    initialize_content: function() {
        this._super();
        var $button = this.$el.find('button');
        $button.click(this.on_button_clicked);
        this.setupFocus($button);
    },

    render_value: function() {
        if (!this.get("effective_readonly")) {
            this._super();
        } else {
            var tmp = this.get('value');
            var s = /(\w+):(.+)|^\.{0,2}\//.exec(tmp);
            if (!s) {
                if (this.get('value')) {
                    tmp = "https://www.crop-r.com/cropr_admin/superboer/" + this.get('value').replace("f","");
                }
            }
            var text = this.get('value');
            this.$el.find('a').attr('href', tmp).text(text);
        }
    },

    on_button_clicked: function() {
        if (!this.get('value')) {
            this.do_warn(_t("Resource Error"), _t("This resource is empty"));
        } else {
            var url = $.trim(this.get('value'));
            if(/^www\./i.test(url))
                url = 'https://www.crop-r.com/cropr_admin/superboer/'+url;
            window.open(url);
        }
    },

});

core.form_widget_registry.add('custom-url', CustomFieldUrl);

});
