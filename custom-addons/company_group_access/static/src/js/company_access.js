odoo.define('company_group_access.company_group_access', function (require) {
"use strict";

var SwitchCompanyMenu = require('web.SwitchCompanyMenu');
var config = require('web.config');
var session = require('web.session');
var rpc = require('web.rpc');

var SwitchCompanyMenuAccess = SwitchCompanyMenu.include({
    init: function () {
        this._super.apply(this, arguments);
        this.isMobile = config.device.isMobile;
        this._onSwitchCompanyClick = _.debounce(this._onSwitchCompanyClick, 1500, true);
        this.allow_user = session.display_switch_company_boolean;
    },
    _onToggleCompanyClick: function (ev) {
        var self = this
        ev.stopPropagation();
        var dropdownItem = $(ev.currentTarget).parent();
        var companyID = dropdownItem.data('company-id');
        var allowed_company_ids = self.allowed_company_ids;
        var current_company_id = allowed_company_ids[0];
        if (dropdownItem.find('.fa-square-o').length) {
            allowed_company_ids.push(companyID);
            dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
        } else {
            allowed_company_ids.splice(allowed_company_ids.indexOf(companyID), 1);
            dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
        }
        setTimeout(function(){
           session.setCompanies(current_company_id, allowed_company_ids);
        },5000);
    },
});

});
