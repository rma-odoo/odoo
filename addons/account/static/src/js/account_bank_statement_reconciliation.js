/* ABOUT
    bankStatementReconciliation is a container for the "single reconciliation" widgets (bankStatementReconciliationLine). The displayed data is retreives from the model as an array of arrays which contains the statement line as first item and an array of move lines as second item. [[st_line, [mv_line, ...]], ...]

    st_line : account.bank.statement.line
    mv_line : account.move.line
*/

/* TODO
    Extraire méthodes de account voucher (load, commit)
    pattern state ?
    create
    change partner :
        - query pour update statement_line (set partner_id = ...)
        - self.start ? Extraire la méthode loadMoveLines
    MVC : méthodes load… ou update… ; les properties appellent les méthodes …changed
    i18n
    demo data
    tests
    
    css transform speed ?
    si montant facture > montant st_line : afficher /!\ jaune : hover "partial reconcile ?", clic split (quelle logique des données ?)
    set as state in bank statement action ; get satetment id via domain field ; place in sheet ; use openerp widgets
    BYE !!! becomes a custom message, with buttons to next probable actions
    
*/

openerp.account = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.account = instance.web.account || {};

    instance.web.client_actions.add('bank_statement_reconciliation_view', 'instance.web.account.bankStatementReconciliation');
    
    instance.web.account.bankStatementReconciliation = instance.web.Widget.extend({
        className: 'oe_bank_statement_reconciliation',
        
        init: function(parent, context) {
            this._super(parent);
            
            this.max_reconciliations_displayed = 3; // Don't wanna congest the page
            this.statement_id = context.context.statement_id;
            this.model_bank_statement = new instance.web.Model("account.bank.statement");
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            
            this.st_lines = []; // The raw data from the model
            this.last_displayed_reconciliation_index = undefined; // Flow control
            this.resolved_lines = 0; // idem
        },
        
        start: function() {
            this._super();
            var self = this;
            
            // Bind keyboard events TODO : méthode standard ?
            $("body").on("keypress", function (e) {
                self.keyboardShortcutsHandler(e);
            });
            
            // Retreive statement infos and reconciliation data from the model
            var deferred_statement = self.model_bank_statement
                .query(["name"])
                .filter([['id', '=', self.statement_id]])
                .first()
                .then(function(statement_name){
                    self.statement_name = statement_name.name;
                });
            var deferred_lines = self.model_bank_statement_line
                .query(['id', 'analytic_account_id', 'ref', 'statement_id', 'sequence', 'type', 'company_id', 'name', 'note', 'journal_id', 'amount', 'date', 'partner_id', 'account_id', 'voucher_id', 'coda_account_number'])
                .filter([['statement_id', '=', self.statement_id]])
                .all().then(function (data) {
                    self.st_lines = data;
                    var reconciliations_to_show = data.slice(0, self.max_reconciliations_displayed);
                    self.last_displayed_reconciliation_index = reconciliations_to_show.length;
                    self.displayReconciliation(reconciliations_to_show.shift(), 'match');
                    _(reconciliations_to_show).each(function(o){ self.displayReconciliation(o, 'inactive'); });
                });
                        
            // When queries are done, render template
            return $.when(deferred_statement, deferred_lines)
                .then(function(){
                    self.$el.prepend(QWeb.render("bank_statement_reconciliation", {statement_name: self.statement_name, total_lines: self.st_lines.length}));
                    // TODO Instancier widget progressbar
                });
        },
        
        // adds fields, prefixed with q_, to the statement line for qweb rendering
        prepareStatementLineForRendering: function(line){
            var self = this;
            line.q_account_num = line.account_id[1].split(' ')[0]; // TODO : get directly account_num by improving get_move_lines ?
            line.q_amount = line.amount.toFixed(2);
            // TODO : label = name + ref ? parent name +"/"+ this.name ?
            line.q_popover = "<table class='details'>\
                <tr><td>Date</td><td>"+line.date+"</td></tr>\
                <tr><td>Nom</td><td>"+line.partner_id[1]+"</td></tr>\
                <tr><td>Type</td><td>"+line.type+"</td></tr>\
                <tr><td>Transaction</td><td>TODO</td></tr>\
                <tr><td>Label</td><td>TODO</td></tr>\
                <tr><td>Montant en &euro;</td><td>"+line.q_amount+"</td></tr>\
                <tr><td>Compte</td><td>"+line.account_id[1]+"</td></tr>\
            </table>";
        },
        
        keyboardShortcutsHandler: function(e) {
            var self = this;
            if (e.which === 13 && (e.ctrlKey || e.metaKey)) {
                $.each(self.getChildren(), function(i, o){
                    o.persistAndDestroy();
                });
            }
        },
        
        displayReconciliation: function(st_line, mode) {
            var self = this;
            self.prepareStatementLineForRendering(st_line);
            new instance.web.account.bankStatementReconciliationLine(self, {st_line: st_line, mode: mode}).appendTo(self.$el);
        },
        
        childValidated: function(child) {
            var self = this;
            
            self.resolved_lines++;
            self.updateProgressbar();
            
            // Display new line if there are left ; say goobye if the work is done
            if (self.last_displayed_reconciliation_index < self.st_lines.length) {
                self.displayReconciliation(self.st_lines[self.last_displayed_reconciliation_index++], 'inactive');
                // TODO : first-child
                var first_child = self.getChildren()[0]; // $.when() ?
                first_child.set("mode", first_child.mode_match);
            } else if (self.resolved_lines === self.st_lines.length) {
                self.$el.append("<br/><br/><center><button class='button_ok'>Success !</button></center>");
                self.$(".button_ok").click(function(){
                    $("body").append("<div style='position: fixed; top: 0;'><div style='margin-left: -1000px; font-weight: bold; font-size: 35em; -webkit-text-stroke: 10px #fff;'>Bye !</div></div>");
                    $("body").animate({padding: 3000}, 1000);
                });
            }
        },
        
        updateProgressbar: function() {
            var self = this;
            var prog_bar = self.$(".progress .progress-bar");
            prog_bar.attr("aria-valuenow", self.resolved_lines);
            prog_bar.css("width", (self.resolved_lines/self.st_lines.length*100)+"%");
            self.$(".progress .progress-text .valuenow").text(self.resolved_lines);
        },
    });
    
    instance.web.account.bankStatementReconciliationLine = instance.web.Widget.extend({
        template: 'bank_statement_reconciliation_line',
        
        events: {
            "click .button_ok": "persistAndDestroy",
            "click .mv_line": "moveLineClickHandler",
            "click .initial_line": "initialLineClickHandler",
            "click .line_open_balance": "lineOpenBalanceClickHandler",
            "click .show_more": "showMoreClickHandler",
            "click .pagerControlLeft:not(.disabled)": "pagerControlLeftHandler",
            "click .pagerControlRight:not(.disabled)": "pagerControlRightHandler",
            "keyup .filter": "filterHandler",
        },
        
        init: function(parent, context) {
            this._super(parent);
            
            this.min_move_lines_displayed = 2;
            this.max_move_lines_displayed = 5;
            this.animation_speed = 300;
            this.st_line = context.st_line;
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            
            this.total_move_lines_num = undefined; // Used for pagers and "show X more"
            this.match_view_folded = undefined;
            
            this.mode_no_partner = 0;
            this.mode_inactive = 1;
            this.mode_match = 2;
            this.mode_create = 3;
            
            this.q_mode = context.mode; // for QWeb ; the mode is applied through an attribute set on the main table
            
            this.set("balance", undefined); // Debit is +, credit is -
            this.set("mode", undefined);
            if (context.mode === 'no_partner') this.set("mode", this.mode_no_partner);
            else if (context.mode === 'inactive') this.set("mode", this.mode_inactive);
            else if (context.mode === 'match') this.set("mode", this.mode_match);
            else if (context.mode === 'create') this.set("mode", this.mode_create);
            this.set("pager_index", 0);
            this.set("mv_lines", []);
            this.set("mv_lines_selected", []);
            this.set("lines_created", []);
        },
        
        start: function() {
            this._super();
            var self = this;
            
            // bins not covered by the events section
            self.bindPopoverTo(self.$(".line_info_button"));
            
            
            // properties
            self.on("change:balance", self, self.balanceChanged);
            self.on("change:mode", self, self.modeChanged);
            self.on("change:pager_index", self, self.pagerChanged);
            self.on("change:mv_lines", self, self.mvLinesChanged);
            self.on("change:mv_lines_selected", self, self.mvLinesSelectedChanged);
            self.on("change:lines_created", self, self.createdLinesChanged);
            
            // load and display
            self.$el.css("opacity", "0");
            $.when(self.loadResolutionProposition()).then(function(){
                $.when(self.updateMatches()).then(function(){
                    self.foldMatchView(0); // TODO : RM (cf showMoreClickHandler)
                    self.$el.animate({opacity: 1}, this.animation_speed);
                });
            });
            
            return; // TODO return what ?
        },
        

        /** Utils */
        
        // adds fields, prefixed with q_, to the move line for qweb rendering
        prepareMoveLineForRendering: function(line){
            var self = this;
            line.q_account_num = line.account_id[1].split(' ')[0];
            line.q_debit = (line.debit === 0 ? "" : line.debit.toFixed(2));
            line.q_credit = (line.credit === 0 ? "" : line.credit.toFixed(2));
            line.q_due_date = (line.date_maturity === false ? line.date : line.date_maturity);
            line.q_popover = "<table class='details'>\
                <tr><td>Account</td><td>"+line.account_id[1]+"</td></tr>\
                <tr><td>Journal</td><td>"+line.journal_id[1]+"</td></tr>\
                <tr><td>Period</td><td>"+line.period_id[1]+"</td></tr>\
                <tr><td>Date</td><td>"+line.date+"</td></tr>\
                <tr><td>Due Date</td><td>"+line.q_due_date+"</td></tr>\
                <tr><td>Amount</td><td>"+(line.q_debit !== "" ? line.q_debit : "")+(line.q_credit !== "" ? "- "+line.q_credit : "")+"</td></tr>\
            </table>";
        },
        
        bindPopoverTo: function(el) {
            var self = this;
            el.popover({
                'placement': 'left',
                'container': self.el,
                'html': true,
                'trigger': 'hover',
                'animation': false,
                'toggle': 'popover'
            });
        },
        
        slideUpTableRow: function($row, speed) {
            var self = this;
            speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);
            
            if ($row.context.dataset.suitableforsliding !== "true") {
                $row.find('td').wrapInner('<div />');
                $row.context.dataset.suitableforsliding = "true";
            }
            $row.find('td > div').slideUp(speed);
            // TODO : td padding
            $row.css("opacity", 1).animate({opacity: 0}, speed/2);
        },
        
        slideDownTableRow: function($row, speed) {
            var self = this;
            speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);
            
            if ($row.context.dataset.suitableforsliding !== "true") {
                $row.find('td').wrapInner('<div />');
                $row.context.dataset.suitableforsliding = "true";
            }
            $row.find('td > div').slideDown(speed);
            $row.css("opacity", 0).animate({opacity: 1}, speed, "easeInCubic");
        },
        
        
        /** Matching */
        
        moveLineClickHandler: function(e) {
            var self = this;
            if (e.currentTarget.dataset.selected === "true") {
                self.deselectMoveLine(e.currentTarget);
            } else {
                self.selectMoveLine(e.currentTarget);
            }
        },
        
        // Takes a move line from the match view and adds it to the mv_lines_selected array
        selectMoveLine: function(mv_line) {
            var self = this;
            var line_id = mv_line.dataset.lineid;
            var line = _.find(self.get("mv_lines"), function(o){ return o.id == line_id; });
            self.set("mv_lines_selected", self.get("mv_lines_selected").concat(line));
        },
        
        // Removes a move line from the mv_lines_selected array
        deselectMoveLine: function(mv_line) {
            var self = this;
            var line_id = mv_line.dataset.lineid;
            self.set("mv_lines_selected", _.filter(self.get("mv_lines_selected"), function(o) { return o.id != line_id; }));
        },
        
        
        /** Matches pagination */
        
        pagerControlLeftHandler: function() {
            var self = this;
            if (self.$(".pagerControlLeft").hasClass("disabled")) { return; /* shouldn't happen, anyway*/ }
            self.set("pager_index", self.get("pager_index")-1 );
        },
        
        pagerControlRightHandler: function() {
            var self = this;
            if (self.$(".pagerControlRight").hasClass("disabled")) { return; /* shouldn't happen, anyway*/ }
            self.set("pager_index", self.get("pager_index")+1 );
        },
        
        filterHandler: function() {
            var self = this;
            self.set("pager_index", 0);
            window.clearTimeout(self.apply_filter_timeout);
            self.apply_filter_timeout = window.setTimeout(self.proxy('updateMatches'), 150);
        },
        
        
        /** Creating */
        
        addLine: function() {
            var self = this;
        },
        
        removeLine: function() {
            var self = this;
        },
        
        
        /** Display */
        
        // Switches between showing min_move_lines_displayed and max_move_lines_displayed
        showMoreClickHandler: function(event) {
            var self = this;
            event.preventDefault();
            
            /* TODO
                should be self.match_view_folded = !self.match_view_folded;
                but foldMatchView needs to be called after updateMatches.
                When folded, lines should be hidden via CSS. (animation callback
                adds or rm the class). Problem is : how to set the css selector
                according to min_move_lines_displayed ?
            */
            
            if (self.match_view_folded) self.unfoldMatchView();
            else self.foldMatchView();
        },
        
        foldMatchView: function(speed) {
            var self = this;
            speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);

            self.$(".match_extended_controls").slideUp(speed, function() { self.$(".match").addClass("folded"); });
            $.each(self.$(".match tr:nth-child(n+"+(self.min_move_lines_displayed+1)+")"), function(i, o) { self.slideUpTableRow($(o), speed); });
            
            if (self.total_move_lines_num <= self.min_move_lines_displayed) {
                self.$(".match .show_more").hide();
            } else {
                self.$(".match .show_more").show().text("Show "+(self.total_move_lines_num !== undefined ? self.total_move_lines_num - self.min_move_lines_displayed : "")+" more");
            }
            self.match_view_folded = true;
        },
        
        unfoldMatchView: function(speed) {
            var self = this;
            speed = typeof speed !== 'undefined' ? speed : self.animation_speed;
            
            self.$(".match_extended_controls").slideDown(speed, function() { self.$(".match").addClass("folded"); });
            $.each(self.$(".match tr:nth-child(n+"+(self.min_move_lines_displayed+1)+")"), function(i, o) { self.slideDownTableRow($(o), speed); });
            
            self.$(".match .show_more").text("Show less");
            self.match_view_folded = false;
        },
        
        initialLineClickHandler: function() {
            var self = this;
            if (self.get("mode") === self.mode_match) {
                self.set("mode", self.mode_inactive);
            } else {
                self.set("mode", self.mode_match);
            }
        },
        
        lineOpenBalanceClickHandler: function() {
            var self = this;
            if (self.get("mode") === self.mode_create) {
                self.set("mode", self.mode_inactive);
            } else {
                self.set("mode", self.mode_create);
            }
        },
        
        showMatchView: function() {
            var self = this;
            self.$(".match").slideDown(self.animation_speed);
            self.$(".toggle_match").css("visibility", "visible")
                                   .css("-webkit-transform", "rotate(90deg)")
                                   .css("-moz-transform", "rotate(90deg)")
                                   .css("-ms-transform", "rotate(90deg)")
                                   .css("transform", "rotate(90deg)");
        },
        
        hideMatchView: function() {
            var self = this;
            self.$(".match").slideUp(self.animation_speed);
            self.$(".toggle_match").css("visibility", "hidden")
                                   .css("-webkit-transform", "rotate(0deg)")
                                   .css("-moz-transform", "rotate(0deg)")
                                   .css("-ms-transform", "rotate(0deg)")
                                   .css("transform", "rotate(0deg)");
        },
        
        showCreateView: function() {
            var self = this;
            self.$(".create").slideDown(self.animation_speed);
            self.$(".toggle_create").css("visibility", "visible")
                                    .css("-webkit-transform", "rotate(90deg)")
                                    .css("-moz-transform", "rotate(90deg)")
                                    .css("-ms-transform", "rotate(90deg)")
                                    .css("transform", "rotate(90deg)");
        },
        
        hideCreateView: function() {
            var self = this;
            self.$(".create").slideUp(self.animation_speed);
            self.$(".toggle_create").css("visibility", "hidden")
                                    .css("-webkit-transform", "rotate(0deg)")
                                    .css("-moz-transform", "rotate(0deg)")
                                    .css("-ms-transform", "rotate(0deg)")
                                    .css("transform", "rotate(0deg)");
        },
        
        
        /** Views updating */
        
        updateAccountingView: function() {
            var self = this;
            self.$(".accounting_view tr:not(.initial_line)").remove();
            
            // Display move lines
            _(self.get("mv_lines_selected")).each(function(line){
                var $line = $(QWeb.render("bank_statement_reconciliation_move_line", {line: line, selected: true}));
                self.bindPopoverTo($line.find(".line_info_button"));
                self.$(".accounting_view").append($line);
            });
            
            // Display created lines
            _(self.added_lines).each(function(line){
                // TODO
            });
        },
        
        updateMatchView: function() {
            var self = this;
            var table = self.$(".match table");
            
            // Display move lines
            table.empty();
            _(self.get("mv_lines")).each(function(line){
                self.prepareMoveLineForRendering(line);
                var $line = $(QWeb.render("bank_statement_reconciliation_move_line", {line: line, selected: false}));
                self.bindPopoverTo($line.find(".line_info_button"));
                table.append($line);
            });
            if (self.match_view_folded) self.foldMatchView(0); // TODO : rm (cf showMoreClickHandler)
        },
        
        updatePagerControls: function() {
            var self = this;
            
            if (self.get("pager_index") === 0)
                self.$(".pagerControlLeft").addClass("disabled");
            else
                self.$(".pagerControlLeft").removeClass("disabled");
            if (self.total_move_lines_num <= ((self.get("pager_index")+1) * self.max_move_lines_displayed))
                self.$(".pagerControlRight").addClass("disabled");
            else
                self.$(".pagerControlRight").removeClass("disabled");
        },
        
        
        /** Model */
        
        // Updates the validation button and the "open balance" line
        balanceChanged: function() {
            var self = this;
            var balance = self.get("balance");
            self.$(".line_open_balance").remove();
            
            if (balance === 0) {
                self.$(".button_ok").addClass("oe_highlight");
                self.$(".button_ok").text("OK");
            } else {
                self.$(".button_ok").removeClass("oe_highlight");
                self.$(".button_ok").text("Keep open");
                var debit = (balance > 0 ? balance.toFixed(2) : "");
                var credit = (balance < 0 ? (-balance).toFixed(2) : "");
                var $line = $(QWeb.render("bank_statement_reconciliation_line_open_balance",
                    
                    // TODO : what ?
                    {debit: credit, credit: debit}));
                self.$(".accounting_view").append($line);
            }
        },
        
        modeChanged: function() {
            var self = this;

            self.$(".action_pane.active").removeClass("active");
            if (self.get("mode") === self.mode_inactive) {
                self.hideMatchView();
                self.hideCreateView(); // TODO returns deferred instead of timeout
                window.setTimeout(function(){ self.el.dataset.mode = "inactive"; }, self.animation_speed);
            } else if (self.get("mode") === self.mode_match) {
                self.showMatchView();
                self.hideCreateView();
                self.$(".action_pane.match").addClass("active");
                window.setTimeout(function(){ self.el.dataset.mode = "match"; }, self.animation_speed);
            } else if (self.get("mode") === self.mode_create) {
                self.hideMatchView();
                self.showCreateView();
                self.$(".action_pane.create").addClass("active");
                window.setTimeout(function(){ self.el.dataset.mode = "create"; }, self.animation_speed);
            }
        },
        
        pagerChanged: function() {
            var self = this;
            self.updateMatches();
        },
        
        mvLinesChanged: function() {
            var self = this;
            self.updateMatchView();
            self.updatePagerControls();
        },
        
        mvLinesSelectedChanged: function() {
            var self = this;
            $.when(self.updateMatches()).then(function(){
                self.updateAccountingView();
                self.updateBalance();
            });
        },
        
        createdLinesChanged: function() {
            var self = this;
            self.updateAccountingView();
            self.updateBalance();
        },
        
        updateBalance: function() {
            var self = this;
            var balance = 0;
            balance -= self.st_line.amount;
            _.each(self.get("mv_lines_selected"), function(o) {
                balance += o.debit;
                balance -= o.credit;
            });
            self.set("balance", balance);
        },
        
        loadResolutionProposition: function() {
            var self = this;
            return self.model_bank_statement_line
                .call("get_resolution_proposition", [self.st_line.id])
                .then(function (lines) {
                    _(lines).each(function(line){ self.prepareMoveLineForRendering(line); });
                    self.set("mv_lines_selected", self.get("mv_lines_selected").concat(lines));
                });
        },
        
        // Loads move lines according to the widget's state
        updateMatches: function() {
            var self = this;
            
            // Load move lines
            var offset = self.get("pager_index") * self.max_move_lines_displayed;
            var filter_str = self.$(".filter").val();
            var mv_lines_selected_ids = _.collect(self.get("mv_lines_selected"), function(o){ return o.id; });
            var deferred_move_lines = self.model_bank_statement_line
                .call("get_move_lines", [self.st_line.id, mv_lines_selected_ids, filter_str, offset, self.max_move_lines_displayed])
                .then(function (lines) {
                    self.set("mv_lines", lines);
                });
            
            // Fetch the number of move lines corresponding to this statement line and this filter
            var deferred_total_move_lines_num = self.model_bank_statement_line
                .call("get_move_lines", [self.st_line.id, mv_lines_selected_ids, filter_str, offset, self.max_move_lines_displayed, true])
                .then(function(num){
                    self.total_move_lines_num = num;
                });
            
            return $.when(deferred_move_lines, deferred_total_move_lines_num).then(function(){
                
                // If pager_index is out of range, set it to display the last page
                if (self.total_move_lines_num <= (self.get("pager_index") * self.max_move_lines_displayed)) {
                    if (self.get("pager_index") !== 0) {
                        self.set("pager_index", Math.ceil(self.total_move_lines_num/self.max_move_lines_displayed)-1);
                    } else {
                        self.foldMatchView();
                    }
                }
            });
        },
        
        // Persist data, notify parent view and terminate widget
        persistAndDestroy: function() {
            var self = this;
            // TODO call
            
            // Prepare sliding animation
            var height = self.$el.outerHeight();
            var container = $("<div />");
            container.css("height", height)
                     .css("marginTop", self.$el.css("marginTop"))
                     .css("marginBottom", self.$el.css("marginBottom"));
            self.$el.wrap(container);
            
            // Bow out
            self.$el.parent().slideUp(self.animation_speed*height/150, function(){
                self.getParent().childValidated(self);
                self.destroy();
            });
            
            
            /*
                // Prepare sliding animation
                var height = self.$el.outerHeight();
                var container = $("<div />");
                container.css("overflow", "hidden")
                         .css("position", "relative")
                         .css("height", height)
                         .css("marginTop", self.$el.css("marginTop"))
                         .css("marginBottom", self.$el.css("marginBottom"));
                self.$el.wrap(container);
                self.$el.css("position", "absolute").css("top", "0px");
                
                // Bow out
                self.$el.animate({top: -height, opacity: 0}, self.animation_speed*height/150);
                self.$el.parent().animate({height: 0}, self.animation_speed*height/150, function(){
                    self.getParent().childValidated(self);
                    self.destroy();
                });
            */
        },
    });
};