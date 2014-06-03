$(document).ready(function() {
    $(".upload_bg_image").change(function(ev){
        var type =  $(this).attr("data-type");
        var id = $(this).attr("data-id");
        $('#back_img').ajaxSubmit({
            data: {
                type: type,
                id: id 
            },
            success: function(data){
                if(type == 'wall'){
                    $("div[name='tweets_for_client']")
                        .animate({opacity: 0.2}, '1500', 
                        function() {
                                $("div[name='tweets_for_client']").css({'background-image': 'url("data:image/jpg;base64,' + data + '")'})
                                .animate({opacity: 1}, '2500');
                        });
                }else{
                    $("tr[data-id=" + id + "] .upload_img").attr('src', 'data:image/jpg;base64,'+data);
                }
            }
        });
    });
    
    if($("div[name='tweets_for_admin']").length){
        var $el = $("div[name='tweets_for_admin']");
        var twitter_wall = new openerp.website.moderate_tweet($el, parseInt($el.attr("wall_id")));
        twitter_wall.start();
    }
    if($("div[name='tweets_for_client']").length){
        var twitter_wall = new openerp.website.tweet_wall($("#tweet_wall_div"), parseInt($("[wall_id]").attr("wall_id")));
        twitter_wall.start();
    }
});

var website = openerp.website;
openerp.website.moderate_tweet = openerp.Class.extend({
    template: 'twitter_moderate_tweets',
    init: function($el, wall_id, interval_time){
        this.$el = $el;
        this.wall_id = parseInt(wall_id);
        this.pending = [];
        this.limit = 20;
        this.new_tweet_id;
        this.check_new_tweet_id;
        this.check_new_tweet_duration = interval_time || 5000;
    },
    start: function(){
        var self = this;
        this.get_data_all();
        this.bind_streaming();
        this.bind_state();
        this.bind_bottom();
        this.bind_new_tweets();
        
        this.$el.find("table[name='published'],table[name='unpublished']").hide();
        this.$el.find("table[name='pending']").show();
        this.$el.find("ul#status li#pending").addClass("active");
        
        this.check_new_tweet_id =  setInterval(function(){
            if(self.pending.length < self.limit){
                return self.check_new_tweet();
            }
        }, this.check_new_tweet_duration);
        
    },
    //Bind for new tweets when encounter
    bind_new_tweets: function(){
        var self = this;
        this.$el.find(".stream-item").click(function(ev){
            $(this).addClass('sr-only');
            self.$el.find("table[name='pending'] tbody tr.alert-success").removeClass('alert-success');
            self.new_tweet_id = self.pending[0]['id'];
            self.process_tweet(self.pending.reverse(), 'pending', 'alert-success');
            self.pending = [];
        });
    },
    
    //Binding States of Twitter pending, accept and reject
    bind_state: function(){
        var self = this;
        this.$el.find('ul#status li a').click(function (e) {
            e.preventDefault();
            $(this).tab('show');
            var state = $(this).parent().attr("id");
            self.$el.find("table#tweet_table").hide();
            self.$el.find("table[name='"+state+"']").show();
            self.$el.find(".load_more_tweet").html('<strong class="glyphicon glyphicon-chevron-down"></strong>');
            if(state == 'published' || state == 'unpublished'){
                self.$el.find("table[name='published'] tbody tr td button[value='published']").hide();
                self.$el.find("table[name='published'] tbody tr td button[value='unpublished']").show();
                self.$el.find("table[name='unpublished'] tbody tr td button[value='unpublished']").hide();
                self.$el.find("table[name='unpublished'] tbody tr td button[value='published']").show();
            }
        });
    },
    
    //For Start and Stop Streaming
    bind_streaming: function(){
        var self = this;
        var $start_stop_button = self.$el.find(".btn-group button");
        $start_stop_button.click(function(){
            var value = $(this).attr("value");
            openerp.jsonRpc("/tweet_moderate/streaming", 'call', {'wall_id' : self.wall_id, 'state' : value}).done(function(state) {
                $start_stop_button.removeClass('stop_streaming start_streaming');
                if(state == 'startstreaming'){
                    $start_stop_button.text("Stop Streaming")
                                 .attr("value", "stopstreaming")
                                 .addClass('stop_streaming btn-danger').removeClass('btn-success');
                    return;
                }
                $start_stop_button.text("Start Streaming")
                                .attr("value", "startstreaming")
                                .addClass('start_streaming btn-success').removeClass('btn-danger');
                
            }).fail(function(){self.error();});
        });
    },
    
    bind_bottom: function(){
        var self = this;
        self.$el.find(".load_more_tweet").click(function(ev){
            var state_item = self.$el.find("#status .active").attr('id');
            var last_tweet_id = self.$el.find("table[name='"+ state_item +"'] tbody tr:last").attr("data-id");
            self.fetch_tweets({'state' : state_item,'last_tweet_id' : last_tweet_id}).done(function(data) {
                    if (data.length){
                        self.process_tweet(data, state_item, '','last')
                        return;
                    }
                    self.$el.find(".load_more_tweet strong").removeClass("glyphicon-refresh glyphicon-chevron-down");
                    self.$el.find(".load_more_tweet strong").text("No more Tweets");
                }).fail(function(){self.error();});
        }); 
    },
    
    check_new_tweet: function(){
        var self = this;
        return this.fetch_tweets({'new_tweet_id' : self.new_tweet_id}).done(function(data) {
                    if (data.length){
                        self.pending = data;
                        self.$el.find(".stream-item").removeClass('sr-only');
                        self.$el.find(".stream-item").find('span strong').text(data.length + " new tweet");
                    }
            }).fail(function(){self.error()});
    },
    
    get_data_all: function(){
        var self = this;
        state = ["pending", "published", "unpublished"];
        state.forEach(function(state_item){
            self.fetch_tweets({'state':state_item}).done(function(data) {
                    if (data.length){
                        if (state_item == 'pending') self.new_tweet_id = data[0].id;
                        self.process_tweet(data.reverse(), state_item);
                    }
            }).fail(function(){self.error();});
        });
    },
    
    fetch_tweets: function(arg){
        var self = this;
        var args = {
                        'wall_id' : self.wall_id, 
                        'published_date' : false, 
                        'state' : 'pending',
                        'fetch_all' : true, 
                        'limit' : self.limit
                    };
        return openerp.jsonRpc("/twitter_wall_tweet_data_admin", 'call', $.extend(args, arg));
    },
    
    //For Binding tweet element like upload, accept, reject button.
    bind_tweet: function(tweet_id){
        var self = this;
        var $tweet = this.$el.find("[data-id=" + tweet_id + "]");
        
        //For upload image
        $tweet.find(".upload_img").click(function(ev){
             self.$el.find("input[type=file]").attr("data-id", tweet_id).click();
        });
        
        //For Accept and Reject Tweets
        $tweet.find(".rowremove").click(function(ev){
            openerp.jsonRpc("/tweet_moderate/state", 'call', {'tweet_id' : parseInt(tweet_id), 'status' : $(this).attr("value")}).done(function(state) {
                $tweet.removeClass('alert-success');
                self.$el.find("table[name='"+state+"'] tbody tr:first").after($tweet.detach());
            }).fail(function(){self.error();});
        });
    },
    
    process_tweet: function(tweets, state, color_class, append){
        var self = this;
        tweets.forEach(function(item){
            var tweet_xml = openerp.qweb.render("twitter_moderate_tweets", {'tweet' : item, 'color_class': color_class || ''});
            self.append_tweet(tweet_xml, item.id, state, append);
        });
    },
    
    append_tweet:function(tweet_xml, tweet_id, state, append){
        var append = append || 'first';
        this.$el.find("table[name='"+state+"'] tbody tr:"+ append).after(tweet_xml);
        this.bind_tweet(tweet_id);
    },
    
    error: function(){
        alert("Unable to reach Server");
    },

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
        self.bind_event();
        self.bind_full_screen();
        this.get_data_interval_id =  setInterval(function(){return self.get_data();}, this.get_data_duration);
        this.show_tweet_interval_id = setInterval(function(){self.process_tweet();}, this.show_tweet_duation);
    },
    
    bind_event: function(){
        $('.upload_img').click(function() {
            $("input[type=file]").click();
        });
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
            str = tweet['tweet'];
            var url_pattern = /(\b(https?):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi;
            str = str.replace(url_pattern, '<span class="tweet_url_hash_highlight">$1</span>');
            
            var hash_pattern = /(\B#\w*[a-zA-Z]+\w*)/gi;
            str = str.replace(hash_pattern, '<span class="tweet_url_hash_highlight">$1</span>');
            
            var uname_pattern = /(\B@\w*[a-zA-Z]+\w*)/gi;
            str = str.replace(uname_pattern, '<span class="tweet_url_hash_highlight">$1</span>');
            tweet['tweet'] = str;

            if(tweet['back_image'])$("div[name='tweets_for_client']").animate({opacity: 0.5}, '1500', function() {
                                                                        $(this).css({'background-image': 'url("data:image/jpg;base64,' + tweet['back_image'] + '")'})
                                                                        .animate({opacity: 1}, '2500');
                                                                });
            this.animate_tweet(openerp.qweb.render("twitter_tweets", {'res' : tweet}));
        }
    },

    
    animate_tweet:function(tweet_html){
        //For more animations
        $(tweet_html).prependTo(this.$el).hide().slideDown("slow");
    },
    
    bind_full_screen: function(){
        $("header").remove();
        $("footer").remove();
        $("#max_window").on('click',function(){
            $("#website-top-navbar").remove();
            // $(".twitter_wall_container").addClass("twitter_wall_container_top");
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
    }
});