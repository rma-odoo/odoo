(function() {
    'use strict';
    
    var website = openerp.website,
        _t = openerp._t;

    /*--------------------------------------------------------------------------
     Template files to load
     --------------------------------------------------------------------------*/
    website.add_template_file('/website/static/src/xml/website.gallery.xml');

    /*--------------------------------------------------------------------------
      Gallery Snippet
      
      This is the snippet responsible for configuring the image galleries.
      Look at /website/views/snippets.xml for the available options
      ------------------------------------------------------------------------*/
    website.snippet.options.gallery = website.snippet.Option.extend({
        start  : function() {
            var self = this;
            this._super();
        },
        styling  : function(type, value) {
            var classes = this.$el.find('li[data-styling]').map(function () {
                return $(this).data('styling');
            }).get().join(' ');
            this.$target.find("img").removeClass(classes).addClass(value);
        },
        interval : function(type, value) {
            this.$target.find('.carousel:first').attr("data-interval", value);
        },
        reapply : function() {
            var self    = this,
                modes   = [ 'nomode', 'grid', 'masonry', 'slideshow' ],
                classes = this.$target.attr("class").split(/\s+/);
            if (this.block) return;
            modes.forEach(function(mode) {
                if (classes.indexOf(mode) != -1) {
                    self[mode]();
                    return;
                }
            });
        },
        get_imgs: function () {
            return this.$target.find("img").addClass("img img-thumbnail img-responsive mb8 mt8").detach();
        },
        mode: function (type, value) {
            if (this.block) return;
            if (!value) value = 'nomode';
            this[value]();
            this.$target.removeClass('nomode masonry grid slideshow').addClass(value);
        },
        replace: function ($content) {
            var $container = this.$target.find(".container:first");
            $container.empty().append($content);
            return $container;
        },
        nomode : function() {
            var self = this,
                $row     = $('<div class="row"></div>'),
                $imgs = this.get_imgs().wrap('<div>').parent();

            this.replace($row);

            $imgs.each(function () {
                var img = this.childNodes[0];
                if (img.width >= img.height * 2) {
                    $(this).addClass("col-md-6");
                } else if (img.width > 600) {
                    $(this).addClass("col-md-6");
                } else {
                    $(this).addClass("col-md-3");
                }
            });
            $row.append($imgs);
        },
        masonry : function() {
            var self     = this,
                $imgs    = this.get_imgs(),
                columns  = this.get_columns(),
                colClass = undefined,
                $cols    = [];

            var $row = $("<div class='row'/>");
            this.replace($row);
            
            // if no columns let's default to 3, here we must update the DOM accordingly :'(
            if (columns === 0) {
                columns = 3;
                this.$target.attr("data-columns", columns);
            }
            colClass = "col-md-"+(12/columns);

            // create columns
            for (var c = 0; c < columns; c++) {
                var $col = $('<div class="col"></div>').addClass(colClass);
                $row.append($col);
                $cols.push($col.get()[0]);
            }

            this.block = true;
            $cols = $($cols);
            var imgs = $imgs.get();
            function add() {
                self.lowest($cols).append(imgs.pop());
                if (imgs.length) setTimeout(add, 0);
                else self.block = false;
            }
            if (imgs.length) add();
        },
        grid : function() {
            var self     = this,
                $imgs    = this.get_imgs().wrap('<div>').parent(),
                $img     = undefined,
                $row     = $('<div class="row"></div>'),
                columns  = this.get_columns() || 3,
                colClass = "col-md-"+(12/columns),
                $container = this.replace($row);

            $imgs.each(function(index) { // 0 based index
                $img = $(this);
                self.img_preserve_styles($img);
                self.img_responsive($img);
                $img.addClass(colClass);
                $img.appendTo($row);
                if ( (index+1) % columns === 0) {
                    $row = $('<div class="row"></div>');
                    $row.appendTo($container);
                }
            });
        },
        slideshow :function () {
            var self = this;
            var $imgs = this.$target.find("img").detach(),
                urls = $imgs.map(function() { return $(this).attr("src"); } ).get(),
                params = {
                        srcs : urls,
                        index: 1,
                        title: "",
                        interval : this.$target.data("interval") || false,
                        id: _.uniqueId("slideshow_")
                },
                $slideshow = $(openerp.qweb.render('website.gallery.slideshow', params));
            this.replace($slideshow);
            $slideshow.css("height", Math.round(window.innerHeight*0.7));
        },
        columns : function(type, value) {
            if (this.block) return;
            this.$target.attr("data-columns", value);
            this.reapply();
        },
        albumimages : function(type, value) {
            if(type === "click") this[value]();
        },
        images_add : function() {
            /* will be moved in ImageDialog from MediaManager */
            var self = this,
                $container = this.$target.find(".container:first"),
                $upload_form = $(openerp.qweb.render('website.gallery.dialog.upload')),
                $progressbar = $upload_form.find(".progress-bar");

            $upload_form.appendTo(document.body);
            
            $upload_form.on('modal.bs.hide', function() { $(this).remove(); } );
            
            $upload_form.find(".alert-success").hide();
            $upload_form.find(".alert-danger").hide();
            $progressbar.hide();

            $upload_form.on("submit", function(event) {
                event.preventDefault();
                $progressbar.show();
                var files = $(this).find('input[type="file"]')[0].files;
                var formData = new FormData();
                for (var i = 0; i < files.length; i++ ) {
                    var file = files[i];
                    formData.append('upload', file, file.name);
                }
                /* 
                 * Images upload : don't change order of contentType & processData
                 * and don't change their values, otherwise the XHR will be 
                 * wrongly conceived by jQuery. 
                 * 
                 * (missing boundary in the content-type header field)
                 * Leading to an upload failure.
                 */
                $.ajax('/website/images_upload', {
                    type: 'POST',
                    data: formData,
                    contentType: false,  /* multipart/form-data for files */
                    processData: false,
                    dataType: 'json',
                    xhrFields: { /* progress bar support */
                        onprogress: function(up) {
                            var pc = Math.floor((up.total / up.totalSize) * 100);
                            var text = " "+pc+" %";
                            $progressbar.css({'width': pc+'%' }).attr("aria-valuenow", pc).text(text);
                        }
                    }
                }).then(
                    
                    function(response) { /* success */
                        $progressbar.addClass("progress-bar-success");
                        $upload_form.find(".alert-success").show();
                        for (var i = 0 ; i < response.length; i++) {
                            $('<img class="img img-thumbnail img-responsive mb8 mt8"/>')
                                .attr("src", response[i].website_url)
                                .appendTo($container);
                        }
                        self.reapply(); // refresh the $target
                    },
                    
                    function(response) { /* failure */
                        $progressbar.addClass("progress-bar-danger");
                        $upload_form.find(".alert-danger").show();
                    }
                );
            });
            $upload_form.modal({ backdrop : false });
            var filepicker = $upload_form.find('input[name="upload"]');
            filepicker.click();
        },
        images_rm   : function() {
            this.replace($('<div class="alert alert-info"/>').text(_t("Add Images from the menu")));
        },
        sizing : function() { // done via css, keep it to avoid undefined error
        },
        /*
         *  helpers
         */
        styles_to_preserve : function($img) {
            var styles = [ 'img-rounded', 'img-thumbnail', 'img-circle', 'shadow', 'fa-spin' ];
            var preserved = [];
            
            for (var style in styles) {
                if ($img.hasClass(style)) {
                    preserved.push(style);
                }
            }
            return preserved.join(' ');
        },
        img_preserve_styles : function($img) {
            var classes = this.styles_to_preserve($img);
            $img.removeAttr("class");
            $img.addClass(classes);
            return $img;
        },
        img_from_src : function(src) {
            var self = this;
            var $img = $("<img/>").attr("src", src);
            return $img;
        },
        img_responsive : function(img) {
            img.addClass("img img-responsive");
            return img;
        },
        lowest : function($cols) {
            var height = 0, min = -1, col=0, lowest = undefined;
            $cols.each(function () {
                var $col = $(this);
                height = $col.height();
                if (min === -1 || height < min) {
                    min = height;
                    lowest = $col;
                }
            });
            return lowest;
        },
        get_columns : function() {
            return parseInt(this.$target.attr("data-columns") || 3);
        },

        clean_for_save: function() {
            var self = this;
            if (this.$target.hasClass("slideshow")) {
                this.$target.removeAttr("style");
            }
        },

        set_active: function () {
            this._super();
            var classes = _.uniq((this.$target.attr("class") || '').split(/\s+/));
            var $li = this.$el.find('[data-mode]')
                .removeClass("active")
                .filter('[data-mode="' + classes.join('"], [data-mode="') + '"]').addClass("active");
            var mode = this.$el.find('[data-mode].active').data('mode');

            var classes = _.uniq((this.$target.find("img:first").attr("class") || '').split(/\s+/));
            var $li = this.$el.find('[data-styling]')
                .removeClass("active")
                .filter('[data-styling="' + classes.join('"], [data-styling="') + '"]').addClass("active");

            this.$el.find('[data-columns]:first, [data-select_class="spc-none"]').parent().parent().toggle(["grid", "masonry"].indexOf(mode) !== -1);

            var interval = this.$target.find('.carousel:first').attr("data-interval");
            var $li = this.$el.find('[data-interval]')
                .removeClass("active")
                .filter('[data-interval=' + interval + ']').addClass("active");

            var columns = this.get_columns();
            var $li = this.$el.find('[data-columns]')
                .removeClass("active")
                .filter('[data-columns=' + columns + ']').addClass("active");
        },
    }); // website.snippet.Option.extend

})(); // anonymous function
