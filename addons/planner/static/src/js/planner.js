(function(){
    "use strict";
    var instance = openerp;
    var QWeb = instance.web.qweb;
    instance.web.Planner = instance.web.WebClient.include({
        show_application: function() {
            var self = this;
            this._super.apply(this, arguments);
            var root_menu = [];
            this.menu.$el.find(".oe_menu_toggler").each(function(el){
                root_menu.push($(this).data('menu'));
            });
            instance.web.planner_manager = new instance.web.PlannerManager();
            var open_menu = self.menu.open_menu;
            self.menu.open_menu = function(){
                open_menu.apply(this, arguments);
                var that = this;
                self.fetch_application_planner().done(function(application){
                    if (_.size(application)) { 
                        instance.web.planner_manager.prependTo(window.$('.oe_systray'));
                        var menu_ids = [];
                        _.each(_.keys(application), function(id){
                             menu_ids.push(parseInt(id, 10));
                        });
                        var id = that.$el.find('.active').children().data("menu");
                        if (_.intersection(menu_ids, root_menu, [id]).length) {
                            instance.web.planner_manager.planner_data = application[id];
                            instance.web.planner_manager.show_planner_tooltip(application[id].tooltip_planner);
                            instance.web.planner_manager.update_progress_value(application[id].progress);
                            instance.web.planner_manager.show();
                        } else {
                            instance.web.planner_manager.hide();
                        }
                    }
                });
            };
        },

        // fetch application planner data only once
        fetch_application_planner: function(){
            self = this;
            var def = $.Deferred();
            if (this.planner_bymenu) {
                def.resolve(self.planner_bymenu);
            } else {
                self.planner_bymenu = {};
                (new instance.web.Model('planner.planner')).query().all().then(function(res) {
                    _(res).each(function(planner) {
                        self.planner_bymenu[planner.menu_id[0]] = planner;
                    });
                    def.resolve(self.planner_bymenu);
                }).fail(function() {def.reject();});
            }
            return def;
        },

    });

    instance.web.PlannerManager = instance.web.Widget.extend({
        template: "PlannerManager",
        events: {
            'click .oe_planner_progress': 'toggle_dialog'
        },

        init: function() {
            this.dialog = new instance.web.PlannerDialog();
            this.dialog.planner_manger = this;
            this.dialog.appendTo(document.body);
        },

        show: function() {
            this.$el.show();
        },

        hide: function() {
            this.$el.hide();
        },

        show_planner_tooltip: function(tooltip) {
            this.$el.find(".progress").tooltip({html: true, title: tooltip, placement: 'bottom', delay: {'show': 500}});
        },

        update_progress_value: function(progress_value) {
            this.$el.find(".progress-bar").css('width', progress_value+"%");
        },

        load_apps:function() {
            return this.planner_data;
        },

        toggle_dialog: function() {
            this.dialog.$('#PlannerModal').modal('toggle');
        },
    });

    instance.web.PlannerDialog = instance.web.Widget.extend({
        template: "PlannerDialog",
        events: {
            'show.bs.modal': 'show',
            'click .oe_planner div[id^="planner_page"] a[href^="#planner_page"]': 'next_page',
            'click .oe_planner li a[data-parent^="#planner_page"]': 'onclick_menu',
            'click .oe_planner div[id^="planner_page"] button[data-progress^="planner_page"]': 'mark_as_done',
        },

        onclick_menu: function(ev) {
            this.$el.find(".oe_planner li a[data-parent^='#planner_page']").parent().removeClass('active');
            this.$el.find(".oe_planner div[id^='planner_page']").removeClass('in');
            this.$el.find(ev.target).parent().addClass('active');
        },

        next_page: function(ev) {
            //find next page
            var next_page_id = $(ev.target).attr('href');
            if (next_page_id) {
                this.$el.find(".oe_planner div[id="+$(ev.target).attr('data-parent')+"]").removeClass('in');
                this.$el.find(".oe_planner li a[data-parent^='#planner_page']").parent().removeClass('active');
                //find active menu
                this.$el.find(".oe_planner li a[data-parent^='#planner_page'][href="+next_page_id+"]").parent().addClass('active')
            }
        },

        mark_as_done: function(ev) {
            var self = this;
            var btn = $(ev.target);
            var active_menu = self.$el.find(".oe_planner li a span[data-check="+btn.attr('data-progress')+"]");
            //get all inputs of current page
            var input_element = self.$el.find(".oe_planner div[id="+btn.attr('data-progress')+"] input[id^='input_element'], select[id^='input_element']");
            var next_button = self.$el.find(".oe_planner a[data-parent="+btn.attr('data-progress')+"]")
            if (!btn.hasClass('fa-check-square-o')) {
                //find menu element and marked as check
                active_menu.addClass('fa-check');
                //mark checked on button
                btn.addClass('fa-check-square-o btn-default').removeClass('fa-square-o btn-primary');
                next_button.addClass('btn-primary').removeClass('btn-default');
                self.update_input_value(input_element, true);
                self.values[btn.attr('id')] = 'checked';
                self.progress = self.progress + 1;
            } else {
                btn.removeClass('fa-check-square-o btn-default').addClass('fa fa-square-o btn-primary');
                next_button.addClass('btn-default').removeClass('btn-primary');
                active_menu.removeClass('fa-check');
                self.values[btn.attr('id')] = '';
                self.update_input_value(input_element, false);
                self.progress = self.progress - 1;
            }
            var data = JSON.stringify(self.values);

            var total_progress = parseInt((self.progress / self.btn_mark_as_done.length) * 100, 10);
            //call rpc to store JSON data in database
            if (data) {
                //update inner and outer progress bar value
                self.update_planner_data(data, total_progress).then(function () {
                    self.planner_manager.update_progress_value(total_progress);
                    self.$el.find(".progress-bar").css('width', total_progress+"%").text(total_progress+"%");
                    self.planner_data['data'] = data;
                    self.planner_data['progress'] = total_progress;
                });
                
            }
        },

        update_input_value: function(input_element, save) {
            _.each(input_element, function(el) {
                var $el = $(el);
                if ($el.attr('type') == 'checkbox' || $el.attr('type') == 'radio') {
                    if ($el.is(':checked') && save) self.values[$el.attr("id")] = 'checked';
                    else self.values[$el.attr("id")] = "";
                } else { 
                    if (save) self.values[$el.attr("id")] = $el.val();
                    else self.values[$el.attr("id")] = "";
                }
            });
        },

        update_planner_data: function(data, progress_value) {
            return (new instance.web.DataSet(this, 'planner.planner'))
                .call('write', [self.planner_data.id,{'data': data, 'progress': progress_value}]);
        },

        load_page: function(template_id) {
            var self = this;
            self.planner_manager = instance.web.planner_manager;
            self.planner_data = self.planner_manager.planner_data;
            self.values = {};
            self.progress = 0;
            this.get_planner_page_template(template_id).then(function(res) {
                self.$('.content').html(res);
                //add footer to each page
                self.add_footer();
                self.input_elements = self.$el.find(".oe_planner input[id^='input_element'], select[id^='input_element']");
                self.btn_mark_as_done = self.$el.find(".oe_planner button[id^='input_element'][data-progress^='planner_page']");
                self.fill_input_data(self.planner_data.data);
                //fill inner progress bar value
                var progress_bar_val = parseInt((self.progress/self.btn_mark_as_done.length)*100);
                self.$el.find(".progress-bar").css('width', progress_bar_val+"%").text(progress_bar_val+"%");
            });
        },

        add_footer: function() {
            var self = this;
            _.each(self.$el.find('.oe_planner div[id^="planner_page"]'), function(el) {
                var $el = $(el);
                var next_page_name = self.$el.find(".oe_planner li a[data-parent='#"+$el.next().attr('id')+"']").text() || ' Finished!';
                var footer_template = QWeb.render("PlannerFooter", {
                    'next_page_name': next_page_name, 
                    'next_page_id': $el.next().attr('id'),
                    'current_page_id': $el.attr('id'),
                    'start': $el.hasClass('start') ? true: false,
                    'end': $el.hasClass('end') ? true: false,
                });
                $el.append(footer_template);
            });
        },

        fill_input_data: function(planner_data) {
            var self = this;
            var input_data = jQuery.parseJSON(self.planner_data.data);
            if (!_.size(input_data)) self.set_all_input_id();
            else self.values = _.clone(input_data);
            _.each(input_data, function(val, id){
                if ($('#'+id).prop("tagName") == 'BUTTON') {
                    if (val == 'checked') {
                        self.progress = self.progress + 1;
                        //checked menu
                        self.$el.find(".oe_planner li a span[data-check="+$('#'+id).attr('data-progress')+"]").addClass('fa-check');
                        var page_id = self.$el.find('#'+id).addClass('fa-check-square-o btn-default').removeClass('fa-square-o btn-primary').attr('data-progress');
                        self.$el.find(".oe_planner .planner_footer a[data-parent="+page_id+"]").addClass('btn-primary').removeClass('btn-default');
                    }
                } else if ($('#'+id).prop("tagName") == 'INPUT' && ($('#'+id).attr('type') == 'checkbox' || $('#'+id).attr('type') == 'radio')) {
                    if (val == 'checked') self.$el.find('#'+id).attr('checked', 'checked');
                } else {
                    self.$el.find('#'+id).val(val);
                }
            });
        },

        set_all_input_id: function() {
            var self = this;
            _.each(self.input_elements, function(el) {
                var $el = $(el);
                if ($el.attr('type') == 'checkbox' || $el.attr('type') == 'radio') self.values[$el.attr("id")] = '';
                else self.values[$el.attr("id")] = $el.val();
            });
            _.each(self.btn_mark_as_done, function(el) {
                var $el = $(el);
                self.values[$el.attr("id")] = '';
            });
        },

        get_planner_page_template: function(template_id) {
            return (new instance.web.DataSet(this, 'ir.ui.view')).call('render', [template_id]);
        },

        show: function() {
            self = this;
            var data = this.planner_manger.load_apps();
            if (data && data.view_id) {
                 self.load_page(data.view_id[0]);
            }
            else return;
        },

    });

})();
