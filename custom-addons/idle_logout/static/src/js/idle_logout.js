odoo.define('idle_logout.BasicController', function (require) {
"use strict";
var BasicController = require('web.BasicController');

var session = require('web.session');

BasicController.include({
    /**
     * add default barcode commands for from view
     *
     * @override
     */
    async willStart () {
        this._super.apply(this, arguments);
        $( document ).idleTimer( 10000 );
        const limitTime = await this.model._rpc({
            model: 'res.users',
            method: 'idle_times',
            args: [[session.uid]],
        });
        console.log("limitTime >>>>>>>>>>>>>>>>>", limitTime)
        if (limitTime !== 0){
            $( document ).idleTimer( limitTime );
            console.log("limitTime <<<<<<<<<<<<<<<<<", limitTime)
            $( document ).on( "idle.idleTimer", function(event, elem, obj){
                // session.session_logout();
                // location.reload();
                setInterval(function () {
                    session.session_logout();
                    location.reload();
                }, limitTime);
            });
        }
    }

});

});
