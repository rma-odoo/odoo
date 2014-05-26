$(document).ready(function() {
    $('.upload_img').click(function() {
        $('input[type=file]').click();
    });
    $('#upload').change(function() {
        $('input[name=func]').val(document.URL);
        $('#back_img').ajaxForm(function() {
            }).submit(); 
    });
    
    if($("div[name='tweets_for_admin']").length){
        var $el = $("div[name='tweets_for_admin']");
        var twitter_wall = new openerp.website.moderate_tweet($el, parseInt($el.attr("wall_id")));
        twitter_wall.start();
    }
    if($("div[name='tweets_for_client']").length){
        var twitter_wall = new openerp.website.tweet_wall($("#tweet_wall_div"), parseInt($("[wall_id]").attr("wall_id")));
        twitter_wall.start();
        //Toggle value
        $("#max_window").on('click',function(){
            if ((document.fullScreenElement && document.fullScreenElement !== null) || (!document.mozFullScreen && !document.webkitIsFullScreen)) {
               if (document.documentElement.requestFullScreen) {
                    document.documentElement.requestFullScreen();
                } else if (document.documentElement.mozRequestFullScreen) {
                    document.documentElement.mozRequestFullScreen();
                } else if (document.documentElement.webkitRequestFullScreen) {
                    document.documentElement.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT);
                }
            } else {
                if (document.cancelFullScreen) {
                    document.cancelFullScreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.webkitCancelFullScreen) {
                    document.webkitCancelFullScreen();
                }
            }
        });
        $("#hide_layout").on('click',function(){
            $("#website-top-navbar").toggle("slow");
            $("header").toggle("slow");
            $(".twitter_wall_container").toggleClass("twitter_wall_container_top");
        });
        $("footer").hide();
    }
    
    $('ul#status li a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    });
});

var website = openerp.website;
var qweb = openerp.qweb;
qweb.add_template('/website_twitter_wall/static/src/xml/website_twitter_wall.xml');
openerp.website.moderate_tweet = openerp.Class.extend({
    template: 'twitter_moderate_tweets',
    init: function($el, wall_id){
        this.$el = $el;
        this.wall_id = wall_id;
        this.pending = [];
    },
    start: function(){
        this.$el.find('table#tweet_table').hide();
        this.get_data();
        this.$el.find("table[name='pending']").show();
    },
    get_data: function(){
        var self = this;
        return openerp.jsonRpc("/twitter_wall_tweet_data_admin", 'call', {'wall_id' : self.wall_id, 'published_date' : false, 'state' : 'pending','fetch_all' : true}).done(function(data) {
                    data.forEach(function(item){
                        console.log(item);
                        var tweet_xml = qweb.render("twitter_moderate_tweets", {'tweet' : item});
                        self.$el.find("table[name='pending'] tbody").append(tweet_xml);
                    });
                });
    },
    process_tweet: function(){
    },
    append_tweet:function(tweet_xml){
    }
    
});
openerp.website.tweet_wall = openerp.Class.extend({
    template : 'twitter_tweets',
    init : function($el, wall_id, interval_time) {
        this.$el = $el;
        this.get_data_duration = interval_time || 5000;
        this.show_tweet_duation = interval_time || 5000;
        this.wall_id = wall_id;
        this.last_publish_date;
        this.show_tweet = [];
        this.shown_tweet = [];
        this.get_data_interval_id;
        this.show_tweet_interval_id;
    },
    start: function(){
        var self = this;
        this.get_data_interval_id =  setInterval(function(){return self.get_data();}, this.get_data_duration);
        this.show_tweet_interval_id = setInterval(function(){self.process_tweet();}, this.show_tweet_duation);
    },
    get_data: function(){
        var self = this;
        if(!this.last_publish_date){
            this.last_publish_date = this.get_current_UTCDate();
        }
        return openerp.jsonRpc("/twitter_wall_tweet_data", 'call', {'wall_id' : self.wall_id, 'published_date' : self.last_publish_date, 'state' : 'published','fetch_all' : false}).done(function(data) {
                    if (data.length){
                        self.last_publish_date = data[data.length - 1].published_date;
                        self.show_tweet = self.show_tweet.concat(data);
                    }
                });
    },
    get_current_UTCDate: function() {
        var d = new Date();
        return d.getUTCFullYear() +"-"+ (d.getUTCMonth()+1) +"-"+d.getUTCDate()+" "+d.getUTCHours()+":"+d.getUTCMinutes()+":"+d.getUTCSeconds()+"."+d.getUTCMilliseconds();
    },
    process_tweet : function() {
        var self = this;
        if (this.show_tweet.length){
            var tweet = self.show_tweet.shift();
            self.shown_tweet.push(tweet);
            console.log(tweet['back_image'])
            if(tweet['back_image']){
                $(".twitter_wall_container").css({
                    'background-image': 'url(data:image/jpg;base64,' + tweet['back_image'] + ')',
                });
                }
            else{
                $(".twitter_wall_container").css({
                    'background-image': "url('/website_twitter_wall/static/src/img/bg.jpg')",
                });
            }
            this.animate_tweet(qweb.render("twitter_tweets", {'res' : tweet}));
        }
    },
    animate_tweet:function(tweet_html){
        //For more animations
        $(tweet_html).prependTo(this.$el).hide().slideDown("slow");
    }
});