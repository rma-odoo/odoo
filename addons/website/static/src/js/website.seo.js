(function () {
    'use strict';
    
    var website = openerp.website;
    website.add_template_file('/website/static/src/xml/website.seo.xml');

    website.seo = {};

    function analyzeKeyword(htmlPage, keyword) {
        return  htmlPage.isInTitle(keyword) ? {
                    title: 'label label-primary',
                    description: "This keyword is used in the page title",
                } : htmlPage.isInDescription(keyword) ? {
                    title: 'label label-info',
                    description: "This keyword is used in the page description",
                } : htmlPage.isInBody(keyword) ? {
                    title: 'label label-info',
                    description: "This keyword is used in the page content."
                } : {
                    title: 'label label-default',
                    description: "This keyword is not used anywhere on the page."
                };
    }

    website.seo.Suggestion = openerp.Widget.extend({
        template: 'website.seo_suggestion',
        events: {
            'click .js_seo_suggestion': 'select',
        },
        init: function (parent, options) {
            this.root = options.root;
            this.language = options.language;
            this.keyword = options.keyword;
            this.htmlPage = options.page;
            this._super(parent);
        },
        start: function () {
            this.htmlPage.on('title-changed', this, this.renderElement);
            this.htmlPage.on('description-changed', this, this.renderElement);
        },
        analyze: function () {
            return analyzeKeyword(this.htmlPage, this.keyword);
        },
        highlight: function () {
            return this.analyze().title;
        },
        tooltip: function () {
            return this.analyze().description;
        },
        select: function () {
            this.trigger('selected', this.keyword, this.language);
        },
    });

    website.seo.SuggestionList = openerp.Widget.extend({
        template: 'website.seo_suggestion_list',
        init: function (parent, options) {
            this.root = options.root;
            this.language = options.language;
            this.htmlPage = options.page;
            this._super(parent);
        },
        start: function () {
            this.refresh();
        },
        refresh: function () {
            var self = this;
            self.$el.append("Loading...");
            function addSuggestions (list) {
                self.$el.empty();
                // TODO Improve algorithm + Ajust based on custom user keywords
                var regex = new RegExp(self.root, "gi");
                var cleanList = _.map(list, function (word) {
                    return word.replace(regex, "").trim();
                });
                // TODO Order properly ?
                _.each(_.uniq(cleanList), function (keyword) {
                    if (keyword) {
                        var suggestion = new website.seo.Suggestion(self, {
                            root: self.root,
                            language: self.language,
                            keyword: keyword,
                            page: self.htmlPage,
                        });
                        suggestion.on('selected', self, function (word, language) {
                            self.trigger('selected', word, language);
                        });
                        suggestion.appendTo(self.$el);
                    }
                });
            }
            var language = this.language ? this.language.split("_") : ["",""];
            $.ajax({
                type: "GET",
                url: "http://google.com/complete/search?output=jsonp&client=youtube&hl="+language[0]+"&q=" +this.root+"&gl="+language[1],
                dataType: "jsonp",            
                success: function (xml) {
                    var suggest_data = [];
                    _.each(xml[1],function(data){
                        suggest_data.push(data[0]);
                    });
                    addSuggestions(suggest_data);
                }
            });
        },
    });

    website.seo.Keyword = openerp.Widget.extend({
        template: 'website.seo_keyword',
        events: {
            'click a[data-action=remove-keyword]': 'destroy',
        },
        maxWordsPerKeyword: 4, // TODO Check
        init: function (parent, options) {
            this.keyword = options.word;
            this.htmlPage = options.page;
            this.language = options.language;
            this._super(parent);
        },
        start: function () {
            this.htmlPage.on('title-changed', this, this.updateLabel);
            this.htmlPage.on('description-changed', this, this.updateLabel);
            this.suggestionList = new website.seo.SuggestionList(this, {
                root: this.keyword,
                language: this.language,
                page: this.htmlPage,
            });
            this.suggestionList.on('selected', this, function (word, language) {
                this.trigger('selected', word, language);
            });
            this.suggestionList.appendTo(this.$('.js_seo_keyword_suggestion'));
        },
        analyze: function () {
            return analyzeKeyword(this.htmlPage, this.keyword);
        },
        highlight: function () {
            return this.analyze().title;
        },
        tooltip: function () {
            return this.analyze().description;
        },
        updateLabel: function () {
            var cssClass = "oe_seo_keyword js_seo_keyword " + this.highlight();
            this.$(".js_seo_keyword").attr('class', cssClass);
            this.$(".js_seo_keyword").attr('title', this.tooltip());
        },
        destroy: function () {
            this.trigger('removed');
            this._super();
        },
    });

    website.seo.KeywordList = openerp.Widget.extend({
        template: 'website.seo_list',
        maxKeywords: 10,
        init: function (parent, options) {
            this.htmlPage = options.page;
            this._super(parent);
        },
        start: function () {
            var self = this;
            var existingKeywords = self.htmlPage.keywords();
            var existinglang = self.htmlPage.language();
            var data = _.object(existingKeywords,existinglang);
            data = _.pairs(data);
            if (existingKeywords.length > 0) {
                _.each(data, function (data) {
                    self.add.call(self, data[0], data[1]);
                });
            } else {
                var companyName = self.htmlPage.company().toLowerCase();
                if (companyName != 'yourcompany') {
                    self.add(companyName);
                }
            }
        },
        keywords: function () {
            var result = [];
            this.$('.js_seo_keyword').each(function () {
                result.push($(this).data('keyword'));
            });
            return result;
        },
        language: function () {
            var result = [];
            this.$('.js_seo_lang').each(function () {
                result.push($(this).data('language'));
            });
            return result;
        },
        isFull: function () {
            return this.keywords().length >= this.maxKeywords;
        },
        exists: function (word, language) {
            var keywordList = this.keywords();
            var languageList = this.language();
            for(var index in keywordList){
                if(word == keywordList[index] && language == languageList[index]){
                    return false;
                }
            }
            return true;
        },
        add: function (candidate, language) {
            var self = this;
            // TODO Refine
            var word = candidate ? candidate.replace(/[,;.:<>]+/g, " ").replace(/ +/g, " ").trim().toLowerCase() : "";
            if (word && !self.isFull() && self.exists(word, language)) {
                var keyword = new website.seo.Keyword(self, {
                    word: word,
                    language: language,
                    page: this.htmlPage,
                });
                keyword.on('removed', self, function () {
                   self.trigger('list-not-full');
                   self.trigger('removed', word);
                });
                keyword.on('selected', self, function (word, language) {
                    self.trigger('selected', word, language);
                });
                keyword.appendTo(self.$el);
            }
            if (self.isFull()) {
                self.trigger('list-full');
            }
        },
    });

    website.seo.Image = openerp.Widget.extend({
        template: 'website.seo_image',
        init: function (parent, options) {
            this.src = options.src;
            this.alt = options.alt;
            this._super(parent);
        },
    });


    website.seo.ImageList = openerp.Widget.extend({
        init: function (parent, options) {
            this.htmlPage = options.page;
            this._super(parent);
        },
        start: function () {
            var self = this;
            this.htmlPage.images().each(function (index, image) {
                new website.seo.Image(self, image).appendTo(self.$el);
            });
        },
        images: function () {
            var result = [];
            this.$('input').each(function () {
               var $input = $(this);
               result.push({
                   src: $input.attr('src'),
                   alt: $input.val(),
               });
            });
            return result;
        },
        add: function (image) {
            new website.seo.Image(this, image).appendTo(this.$el);
        },
    });

    website.seo.Preview = openerp.Widget.extend({
        template: 'website.seo_preview',
        init: function (parent, options) {
            this.title = options.title;
            this.url = options.url;
            this.description = options.description || "[ The description will be generated by google unless you specify one ]";
            this._super(parent);
        },
    });

    website.seo.HtmlPage = openerp.Class.extend(openerp.PropertiesMixin, {
        url: function () {
            var url = window.location.href;
            var hashIndex = url.indexOf('#');
            return hashIndex >= 0 ? url.substring(0, hashIndex) : url;
        },
        title: function () {
            var $title = $('title');
            return ($title.length > 0) && $title.text() && $title.text().trim();
        },
        changeTitle: function (title) {
            // TODO create tag if missing
            $('title').text(title);
            this.trigger('title-changed', title);
        },
        description: function () {
            var $description = $('meta[name=description]');
            return ($description.length > 0) && ($description.attr('content') && $description.attr('content').trim());
        },
        changeDescription: function (description) {
            // TODO create tag if missing
            $('meta[name=description]').attr('content', description);
            this.trigger('description-changed', description);
        },
        keywords: function () {
            var $keywords = $('meta[name=keywords]');
            var parsed = ($keywords.length > 0) && $keywords.attr('content') && $keywords.attr('content').split(",");
            return (parsed && parsed[0]) ? parsed: [];
        },
        language: function () {
            var $lang = $('meta[name=language]');
            var parsed = ($lang.length > 0) && $lang.attr('content') && $lang.attr('content').split(",");
            return (parsed && parsed[0]) ? parsed: [];
        },
        changeKeywords: function (keywords) {
            // TODO create tag if missing
            $('meta[name=keywords]').attr('content', keywords.join(","));
            this.trigger('keywords-changed', keywords);
        },
        changeLanguage: function (language) {
            $('meta[name=language]').attr('content', language.join(","));
            this.trigger('language-changed', language);
        },
        headers: function (tag) {
            return $('#wrap '+tag).map(function () {
                return $(this).text();
            });
        },
        images: function () {
            return $('#wrap img').map(function () {
                var $img = $(this);
                return  {
                    src: $img.attr('src'),
                    alt: $img.attr('alt'),
                };
            });
        },
        company: function () {
            return $('html').attr('data-oe-company-name');
        },
        bodyText: function () {
            return $('body').children().not('.js_seo_configuration').text();
        },
        isInBody: function (text) {
            return new RegExp("\\b"+text+"\\b", "gi").test(this.bodyText());
        },
        isInTitle: function (text) {
            return new RegExp("\\b"+text+"\\b", "gi").test(this.title());
        },
        isInDescription: function (text) {
            return new RegExp("\\b"+text+"\\b", "gi").test(this.description());
        },
    });

    website.seo.Tip = openerp.Widget.extend({
        template: 'website.seo_tip',
        events: {
            'closed.bs.alert': 'destroy',
        },
        init: function (parent, options) {
            this.message = options.message;
            // cf. http://getbootstrap.com/components/#alerts
            // success, info, warning or danger
            this.type = options.type || 'info';
            this._super(parent);
        },
    });

    website.seo.Configurator = openerp.Widget.extend({
        template: 'website.seo_configuration',
        events: {
            'keyup input[name=seo_page_keywords]': 'confirmKeyword',
            'keyup input[name=seo_page_title]': 'titleChanged',
            'keyup textarea[name=seo_page_description]': 'descriptionChanged',
            'click button[data-action=add]': 'addKeyword',
            'click button[data-action=update]': 'update',
            'hidden.bs.modal': 'destroy',
        },
        canEditTitle: false,
        canEditDescription: false,
        canEditKeywords: false,
        canEditLanguage: false,
        maxTitleSize: 65,
        maxDescriptionSize: 150,
        start: function () {
            var self = this;
            var $modal = self.$el;
            var htmlPage = this.htmlPage = new website.seo.HtmlPage();
            $modal.find('.js_seo_page_url').text(htmlPage.url());
            $modal.find('input[name=seo_page_title]').val(htmlPage.title());
            $modal.find('textarea[name=seo_page_description]').val(htmlPage.description());
            // self.suggestImprovements();
            // self.imageList = new website.seo.ImageList(self, { page: htmlPage });
            // if (htmlPage.images().length === 0) {
            //     $modal.find('.js_image_section').remove();
            // } else {
            //     self.imageList.appendTo($modal.find('.js_seo_image_list'));
            // }
            self.keywordList = new website.seo.KeywordList(self, { page: htmlPage });
            self.keywordList.on('list-full', self, function () {
                $modal.find('input[name=seo_page_keywords]')
                    .attr('readonly', "readonly")
                    .attr('placeholder', "Remove a keyword first");
                $modal.find('button[data-action=add]')
                    .prop('disabled', true).addClass('disabled');
            });
            self.keywordList.on('list-not-full', self, function () {
                $modal.find('input[name=seo_page_keywords]')
                    .removeAttr('readonly').attr('placeholder', "");
                $modal.find('button[data-action=add]')
                    .prop('disabled', false).removeClass('disabled');
            });
            self.keywordList.on('selected', self, function (word, language) {
                self.keywordList.add(word, language);
            });
            self.keywordList.appendTo($modal.find('.js_seo_keywords_list'));
            self.disableUnsavableFields();
            self.renderPreview();
            $modal.modal();
            self.getLanguages();
        },
        getLanguages: function(){
            var self = this;
            openerp.jsonRpc("/website/scan_languages","call",{}).then(function(result){
                var default_lang = website.get_context().lang;
                _.each(result, function(data){
                    if(default_lang == data[0]){
                        self.$('#language-box')
                        .append($('<option selected></option>')
                        .attr('value',data[0])
                        .text(data[1]));
                    }
                    else {
                    self.$('#language-box')
                        .append($('<option></option>')
                        .attr('value',data[0])
                        .text(data[1]));
                    }
                });
            });
        },
        disableUnsavableFields: function () {
            var self = this;
            var $modal = self.$el;
            self.loadMetaData().then(function (data) {
                self.canEditTitle = data && ('website_meta_title' in data);
                self.canEditDescription = data && ('website_meta_description' in data);
                self.canEditKeywords = data && ('website_meta_keywords' in data);
                self.canEditLanguage = data && ('website_meta_language' in data);
                if (!self.canEditTitle) {
                    $modal.find('input[name=seo_page_title]').attr('disabled', true);
                }
                if (!self.canEditDescription) {
                    $modal.find('textarea[name=seo_page_description]').attr('disabled', true);
                }
                if (!self.canEditTitle && !self.canEditDescription && !self.canEditKeywords) {
                    $modal.find('button[data-action=update]').attr('disabled', true);
                }
            });
        },
        suggestImprovements: function () {
            var tips = [];
            var self = this;
            function displayTip(message, type) {
                new website.seo.Tip(self, {
                   message: message,
                   type: type,
                }).appendTo(self.$('.js_seo_tips'));
            }
            var htmlPage = this.htmlPage;

            // Add message suggestions at the top of the dialog
            // if necessary....
            // if (htmlPage.headers('h1').length === 0) {
            //     tips.push({
            //         type: 'warning',
            //         message: "This page seems to be missing a title.",
            //     });
            // }

            if (tips.length > 0) {
                _.each(tips, function (tip) {
                    displayTip(tip.message, tip.type);
                });
            }
        },
        confirmKeyword: function (e) {
            if (e.keyCode == 13) {
                this.addKeyword();
            }
        },
        addKeyword: function (word) {
            var $input = this.$('input[name=seo_page_keywords]');
            var $language = this.$('select[name=seo_page_language]');
            var keyword = _.isString(word) ? word : $input.val();
            var language = _.isString(word) ? word : $language.val().toLowerCase();
            this.keywordList.add(keyword,language);
            $input.val("");
            this.getLanguages();
        },
        update: function () {
            var self = this;
            var data = {};
            if (self.canEditTitle) {
                data.website_meta_title = self.htmlPage.title();
            }
            if (self.canEditDescription) {
                data.website_meta_description = self.htmlPage.description();
            }
            if (self.canEditKeywords) {
                data.website_meta_keywords = self.keywordList.keywords().join(", ");
            }
            if(self.canEditLanguage){
                data.website_meta_language = self.keywordList.language().join(",");
            }
            self.saveMetaData(data).then(function () {
               self.$el.modal('hide');
            });
        },
        getMainObject: function () {
            var repr = $('html').data('main-object');
            var m = repr.match(/(.+)\((\d+),(.*)\)/);
            if (!m) {
                return null;
            } else {
                return {
                    model: m[1],
                    id: m[2]|0
                };
            }
        },
        loadMetaData: function () {
            var self = this;
            var obj = this.getMainObject();
            var def = $.Deferred();
            if (!obj) {
                // return $.Deferred().reject(new Error("No main_object was found."));
                def.resolve(null);
            } else {
                var fields = ['website_meta_title', 'website_meta_description', 'website_meta_keywords', 'website_meta_language'];
                var model = website.session.model(obj.model);
                model.call('read', [[obj.id], fields, {'website_id':website.get_context().website_id}]).then(function (data) {
                    if (data.length) {
                        var meta = data[0];
                        meta.model = obj.model;
                        def.resolve(meta);
                    } else {
                        def.resolve(null);
                    }
                }).fail(function () {
                    def.reject();
                });
            }
            return def;
        },
        saveMetaData: function (data) {
            var obj = this.getMainObject();
            if (!obj) {
                return $.Deferred().reject();
            } else {
                var model = website.session.model(obj.model);
                return model.call('write', [[obj.id], data, {'website_id':website.get_context().website_id}]);
            }
        },
        titleChanged: function () {
            var self = this;
            setTimeout(function () {
                var title = self.$('input[name=seo_page_title]').val();
                self.htmlPage.changeTitle(title);
                self.renderPreview();
            }, 0);
        },
        descriptionChanged: function () {
            var self = this;
            setTimeout(function () {
                var description = self.$('textarea[name=seo_page_description]').attr('value');
                self.htmlPage.changeDescription(description);
                self.renderPreview();
            }, 0);
        },
        renderPreview: function () {
            var preview = new website.seo.Preview(this, {
                title: this.htmlPage.title(),
                description: this.htmlPage.description(),
                url: this.htmlPage.url(),
            });
            var $preview = this.$('.js_seo_preview');
            $preview.empty();
            preview.appendTo($preview);
        },
        destroy: function () {
            this.htmlPage.changeKeywords(this.keywordList.keywords());
            this.htmlPage.changeLanguage(this.keywordList.language());
            this._super();
        },
    });

    website.ready().done(function() {
        $(document.body).on('click', 'a[data-action=promote-current-page]', function() {
            new website.seo.Configurator(this).appendTo($(document.body));
        });
    });

})();
