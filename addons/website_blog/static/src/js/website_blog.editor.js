(function() {
    "use strict";
    var cover_resize_class = "";
    var cover_background = "#000000 none";
    var cover_opacity = 1.0;
    var website = openerp.website;
    var _t = openerp._t;

    website.EditorBarContent.include({
        new_blog_post: function() {
            website.session.model('blog.blog').call('name_search', [], { context: website.get_context() })
            .then(function(cat_id) {
                if (cat_id.length <= 1) {
                    document.location = '/blogpost/new?blog_id=' + cat_id[0][0];
                }
                else {
                    website.prompt({
                        id: "editor_new_blog",
                        window_title: _t("New Blog Post"),
                        select: "Select Blog",
                        init: function (field) {
                          return website.session.model('blog.blog')
                            .call('name_search', [], { context: website.get_context() });
                        },
                    }).then(function (cat_id) {
                        document.location = '/blogpost/new?blog_id=' + cat_id;
                      });
                }
            });    
        },
    });

    website.EditorBar.include({
        edit: function () {
            var self = this;
            $('.popover').remove();
            this._super();
            var vHeight = $(window).height();
            $('body').on('click','#change_cover',_.bind(this.change_bg, self.rte.editor, vHeight));
            $('body').on('click', '#clear_cover',_.bind(this.clean_bg, self.rte.editor, vHeight));
            $('body').on('click mouseover', 'ul.cover_resize li',_.bind(this.cover_resize_mouseover, self.rte.editor));
            $('body').on('mouseleave', 'ul.cover_resize li:not(.active)',_.bind(this.cover_resize_mouseleave, self.rte.editor));
            $('body').on('click mouseover', 'ul.cover_background li',_.bind(this.cover_background_mouseover, self.rte.editor));
            $('body').on('mouseleave', 'ul.cover_background li:not(.active)',_.bind(this.cover_background_mouseleave, self.rte.editor));
            $('body').on('click mouseover', 'ul.cover_opacity li',_.bind(this.cover_opacity_mouseover, self.rte.editor));
            $('body').on('mouseleave', 'ul.cover_opacity li:not(.active)',_.bind(this.cover_opacity_mouseleave, self.rte.editor));
            $(document.body).on('media-saved', self, function (o) {
                $.blockUI.defaults.css = { width: '30%',top: '40%',left: '35%',textAlign: 'center',color:'#FFFFFF'};
                $.blockUI({ message: '<div><i class="fa fa-spinner fa-5x fa-spin"></i><br/>Uploading...' }); 
                $('ul.cover_background li').removeClass("active");
                var url = $('.cover-storage').attr('src');
                $('.js_fullheight').css({"background": !_.isUndefined(url) ? 'rgb(8,8,8) url(' + url + ')  repeat scroll 0% 0% / cover' : "pink", 'min-height': vHeight});
                $('.cover-storage').replaceWith("<div class='cover-storage oe_hidden'></div>");
                cover_background = $('.js_fullheight').css("background");
                $.unblockUI();
            });            
            cover_resize_class = $('#title').attr("class");
            cover_background = $(".js_fullheight").get(0).style.background;
            cover_opacity = $(".js_fullheight").css("opacity");           
        },
        save : function() {
            var res = this._super();
            if ($('.cover').length) {
                openerp.jsonRpc("/blogpost/change_background", 'call', {
                    'post_id' : $('#blog_post_name').attr('data-oe-id'),
                    'cover_info' : '{"background": "'+ $('.js_fullheight').get(0).style.background.replace(/"/g,'') +'","opacity":"'+ cover_opacity +'","resize_class": "'+cover_resize_class + '"}', 
                });
            }
            return res;
        },
        clean_bg : function(vHeight) {
            $('.js_fullheight').css({"background":'none', 'opacity':1, 'min-height': vHeight});
        },
        cover_resize_mouseover : function(e) {
          if(e.type=="click"){
               $('ul.cover_resize li').removeClass("active");
               $('#' + e.target.id).parent().addClass("active");
               $('#title').attr("class" ,"cover " + e.target.id)
               cover_resize_class = $('#title').attr("class");
           }
           else
           {
               $('#title').attr("class" ,"cover " + e.target.id)
           }
        }, 
        cover_resize_mouseleave : function(e) {
            $('#title').attr("class",cover_resize_class);  
        },
        cover_opacity_mouseover : function(e) {
          if(e.type=="click"){
               $('ul.cover_opacity li').removeClass("active");
               $('#' + e.target.id).parent().addClass("active");
               $('.js_fullheight').css("opacity",e.target.id);
               cover_opacity = $('.js_fullheight').css("opacity");
           }
           else
           {
                $('.js_fullheight').css("opacity",e.target.id);
           }
        }, 
        cover_opacity_mouseleave : function(e) {
            $('.js_fullheight').css("opacity",cover_opacity);
        },        
        cover_background_mouseover : function(e) {
          if(e.type=="click"){
              $('ul.cover_background li').removeClass("active");
              $('#' + e.target.id).parent().addClass("active");
              $('.js_fullheight').css("background",e.target.id);
              cover_background = e.target.id;
          }
          else
          {               
              $('.js_fullheight').css("background",e.target.id);
          }
        }, 
        cover_background_mouseleave : function(e) {
          $('.js_fullheight').css("background",cover_background);
        },                        
        change_bg : function(vHeight) {
            var self  = this;
            var element = new CKEDITOR.dom.element(self.element.find('.cover-storage').$[0]);
            var editor  = new website.editor.MediaDialog(self, element);
            editor.appendTo('body');
        },
    });
})();
