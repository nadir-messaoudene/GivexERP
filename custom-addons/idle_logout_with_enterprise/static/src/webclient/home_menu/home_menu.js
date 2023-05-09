/** @odoo-module **/

import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";
import { patch } from 'web.utils';

import { loadAssets } from "@web/core/assets";
import session from 'web.session';
import rpc from 'web.rpc';

patch(HomeMenu.prototype, 'idle_logout_with_enterprise/static/src/webclient/home_menu/home_menu.js', {

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Override to include livechat channels.
     *
     * @override
     */
    async willStart() {
        const res = await this._super(...arguments);
        const assets = loadAssets({
            jsLibs: ["/idle_logout/static/lib/idle_timer/jquery.idle_timer.js"],
        });
        await assets;
        $( document ).idleTimer( 10000 );
        const limitTime = await rpc.query({
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
            return res;
        }
    },

});
