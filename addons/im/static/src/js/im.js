(function() {
    var im = openerp.im = {};

    im.ERROR_DELAY = 30000;

    im.Bus = openerp.Widget.extend({
        init: function(){
            this._super();
            this.options = {};
            this.activated = false;
            this.channels = [];
            this.last = 0;
        },
        start_polling: function(){
            if(!this.activated){
                this.poll();
            }
        },
        poll: function() {
            var self = this;
            self.activated = true;
            var data = {'channels': self.channels, 'last': self.last, 'options' : self.options};
            //console.log("########### POLL : ", JSON.stringify(data));
            openerp.jsonRpc('/longpolling/poll', 'call', data).then(function(result) {
                _.each(result, _.bind(self.on_notification, self));
                self.poll();
            }, function(unused, e) {
                //e.preventDefault();
                setTimeout(_.bind(self.poll, self), im.ERROR_DELAY);
            });
        },
        on_notification: function(notification) {
            //console.log("################## NOTIF", JSON.stringify(notification));
            if (notification.id > this.last) {
                this.last = notification.id;
            }
            this.trigger("notification", [notification.channel, notification.message]);
        },
        add_channel: function(channel){
            if(!_.contains(this.channels, channel)){
                this.channels.push(channel);
            }
        },
        delete_channel: function(channel){
            this.channels = _.without(this.channels, channel);
        },
    });

    // singleton
    im.bus = new im.Bus();
    return im;
})();