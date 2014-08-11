(function(){
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;
    website.add_template_file('/website_slides/static/src/xml/website_slides.xml');

    website.EditorBarContent.include({
        new_slide: function() {
            new website.editor.AddSlideDialog(this).appendTo(document.body);
        },

    });
    website.editor.AddSlideDialog = website.editor.Dialog.extend({
        template: 'website.addslide.dialog',
        events: _.extend({}, website.editor.Dialog.prototype.events, {
            'change .slide-upload': 'slide_upload',
        }),
        init: function(){
            this._super.apply(this, arguments);
            this.file = {};
        },

        start: function (){
            this.$('.save').text('Create Slide');
            var r = this._super.apply(this, arguments);
            this.set_tags("");
            return r;
        },
        slide_upload: function(ev){
            var self = this;
            var file = ev.target.files[0];
            var ArrayReader = new FileReader();
            var BinaryReader = new FileReader();
            // file read as DataURL
            BinaryReader.readAsDataURL(file);
            BinaryReader.onloadend = function(upload) {
                var buffer = upload.target.result;
                buffer = buffer.split(',')[1];
                self.file.data = buffer;
                self.file.name = file.name;
            };
            // file read as ArrayBuffer for PDFJS get_Document API
            ArrayReader.readAsArrayBuffer(file);
            ArrayReader.onload = function(evt) {
                var buffer = evt.target.result;
                // PDFJS can't eval path because of bundle assest
                // https://github.com/mozilla/pdf.js/blob/master/src/pdf.js#L41
                var path = '';
                var pathArray = window.location.pathname.split( '/' );
                pathArray.forEach(function(){path +='../'});
                PDFJS.workerSrc = path + 'website_slides/static/lib/pdfjs/build/pdf.worker.js';

                PDFJS.getDocument(buffer).then(function getPdf(pdf) {
                    pdf.getPage(1).then(function getFirstPage(page) {
                        var scale = 1;
                        var viewport = page.getViewport(scale);
                        var canvas = document.getElementById('the-canvas');
                        var context = canvas.getContext('2d');
                        canvas.height = viewport.height;
                        canvas.width = viewport.width;
                        //
                        // Render PDF page into canvas context
                        //
                        page.render({canvasContext: context, viewport: viewport});
                    });
                });
            };
        },

        set_tags: function(tags){
            this.$("input.slide-tags").textext({
                plugins: 'tags focus autocomplete ajax',
            tagsItems: tags.split(","),
            // Note: The following list of keyboard keys is added. All entries are default except {32 : 'whitespace!'}.
            keys: {8: 'backspace', 9: 'tab', 13: 'enter!', 27: 'escape!', 37: 'left', 38: 'up!', 39: 'right',
                40: 'down!', 46: 'delete', 108: 'numpadEnter', 32: 'whitespace!'},
            ajax: {
                url: '/slides/get_tags',
            dataType: 'json',
            cacheResults: true
            }
            });
        },
        get_value: function(){
            var self = this;
            var default_val = {
                'is_slide': true,
                'website_published': false, 
            };
            var values = {
                'name' : this.$('#name').val(),
                'description' : this.$('#description').val(),
                //'tags' : this.$('.slide-tags').textext()[0].tags()._formData,
                'datas': self.file.data,
                'datas_fname': self.file.name,
                'image': this.$('#the-canvas')[0].toDataURL().split(',')[1],
                'url': this.$('#url').val()
            };
            return _.extend(values, default_val);
        },
        save: function () {
            var values = this.get_value();
            website.form('/slides/add_slide', 'POST', values);
        },


    });

})();
