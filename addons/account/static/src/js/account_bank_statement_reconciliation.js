/* ABOUT
    bankStatementReconciliation is a container for the "single reconciliation" widgets (bankStatementReconciliationLine). The displayed data is retreives from the model as an array of arrays which contains the statement line as first item and an array of move lines as second item. [[st_line, [mv_line, ...]], ...]

    st_line : account.bank.statement.line
    mv_line : account.move.line
*/

/* TODO
    Extraire méthodes de account voucher (load, commit)
    flicker ?
    progressbar jquery
    change partner et no_partner
    ctrl-enter
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
            
            this.st_lines = []; // The raw data from the model
            this.last_displayed_reconciliation_index = undefined; // Flow control
            this.resolved_lines = 0; // idem
        },
        
        start: function() {
            this._super();
            var self = this;
            var display = self.displayReconciliation.bind(self);
            
            // Retreive statement infos and reconciliation data from the model
            var deferred_statement = self.model_bank_statement
                .query(["name"])
                .filter([['id', '=', self.statement_id]])
                .first()
                .then(function(statement_name){
                    self.statement_name = statement_name.name;
                });
            var deferred_lines = self.model_bank_statement
                .call("get_lines", [self.statement_id])
                .then(function (data) {
                    self.st_lines = data;
                    var reconciliations_to_show = data.slice(0, self.max_reconciliations_displayed);
                    _(reconciliations_to_show).each(display);
                    self.last_displayed_reconciliation_index = reconciliations_to_show.length;
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
        
        displayReconciliation: function(st_line) {
            var self = this;
            self.prepareStatementLineForRendering(st_line);
            // TODO pas envie de garder la référence
            new instance.web.account.bankStatementReconciliationLine(self, {st_line: st_line}).appendTo(self.$el);
        },
        
        childValidated: function(child) {
            var self = this;
            var display = self.displayReconciliation.bind(self);
            
            self.resolved_lines++;
            self.updateProgressbar();
            
            // Display new line if there are left ; say goobye if the work is done
            if (self.last_displayed_reconciliation_index < self.st_lines.length) {
                display(self.st_lines[self.last_displayed_reconciliation_index++]);
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
            var prog_bar = self.$(".global_progress");
            prog_bar.attr("value", self.resolved_lines);
            prog_bar.text((self.resolved_lines / self.st_lines.length) + "%");
        },
    });
    
    instance.web.account.bankStatementReconciliationLine = instance.web.Widget.extend({
        template: 'bank_statement_reconciliation_line',
        
        events: {
            "click .button_ok": "persistAndDestroy",
            "click .mv_line": "moveLineClickHandler",
            "click .line_open_balance": "lineOpenBalanceHandler",
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
        },
        
        start: function() {
            this._super();
            var self = this;
            
            // bind events on the statement line
            self.bindPopoverTo(self.$(".line_info_button"));
            
            // properties
            self.set("pager_index", 0);
            self.on("change:pager_index", self, self.updateMatches);
            self.set("mv_lines", []);
            self.on("change:mv_lines", self, self.updateMatchView);
            self.set("mv_lines_selected", []);
            self.on("change:mv_lines_selected", self, self.updateAccountingView);
            self.set("lines_created", []);
            self.on("change:lines_created", self, self.updateAccountingView);
            
            // Load the resolution proposition
            var deferred_resolution_proposition = self.model_bank_statement_line
                .call("get_resolution_proposition", [self.st_line.id])
                .then(function (lines) {
                    _(lines).each(function(line){ self.prepareMoveLineForRendering(line); });
                    self.set("mv_lines_selected", self.get("mv_lines_selected").concat(lines));
                    
                    // Load move lines and set up the match view
                    $.when(self.updateMatches()).then(function(){
                        self.foldMatchView(0);
                    });
                });
            
            // TODO Doesn't include the deferred from self.updateMatches
            return deferred_resolution_proposition;
        },
        
        
        /** Utils
            Useful misc stuffs
        */
        
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
            
            // Should check for all td
            if ($row.find("td > div").length === 0) { $row.find('td').wrapInner('<div></div>'); }
            $row.find('td > div').slideUp(speed, function(){/* return deferred ?*/});
        },
        
        slideDownTableRow: function($row, speed) {
            var self = this;
            speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);
            
            // Should check for all td
            if ($row.find("td > div").length === 0) {$row.find('td').wrapInner('<div></div>');}
            $row.find('td > div').slideDown(speed, function(){/* return deferred ?*/});
        },
        
        
        /** Matching
            Functions related to the matching of existing move lines
        */
        
        moveLineClickHandler: function(e) {
            var self = this;
            if (e.currentTarget.dataset.selected === "true") {
                self.deselectMoveLine(e.currentTarget); // TODO
            } else {
                self.selectMoveLine(e.currentTarget);
            }
        },
        
        // Takes a move line from the match view and adds it to the mv_lines_selected array, triggering view update
        selectMoveLine: function($mv_line) {
            var self = this;
            var line_id = $mv_line.dataset.lineid;
            var line = _.find(self.get("mv_lines"), function(o){ return o.id == line_id; });
            self.set("mv_lines_selected", self.get("mv_lines_selected").concat(line));
            self.updateMatches();
        },
        
        // Removes a move line from the mv_lines_selected array, triggering view update
        deselectMoveLine: function($mv_line) {
            var self = this;
            var line_id = $mv_line.dataset.lineid;
            self.set("mv_lines_selected", _.filter(self.get("mv_lines_selected"), function(o) { return o.id != line_id; }));
            self.updateMatches();
        },
        
        
        /** Creating
            Functions related to the creation of new move lines
        */
        
        lineOpenBalanceHandler: function() {
        
        },
        
        addLine: function() {
            var self = this;
        },
        
        removeLine: function() {
            var self = this;
        },
        
        
        /** Display
            Functions for controlling the widget's appareance
        */
        
        // Switches between showing min_move_lines_displayed and max_move_lines_displayed
        showMoreClickHandler: function(event) {
            var self = this;
            event.preventDefault();
            // self.match_view_folded = !self.match_view_folded;
            if (self.match_view_folded)
                self.unfoldMatchView();
            else
                self.foldMatchView();
        },
        
        foldMatchView: function(speed) {
            var self = this;
            speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);

            self.$(".match_extended_controls").slideUp(speed, function() { self.$(".match").addClass("folded"); });
            $.each(self.$(".match tr:nth-child(n+3)"), function(i, o) { self.slideUpTableRow($(o), speed); });
            
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
            $.each(self.$(".match tr:nth-child(n+3)"), function(i, o) { self.slideDownTableRow($(o), speed); });
            
            self.$(".match .show_more").text("Show less");
            self.match_view_folded = false;
        },
        
        showMatchView: function() {
            var self = this;
        },
        
        hideMatchView: function() {
            var self = this;
        },
        
        showCreateView: function() {
            var self = this;
        },
        
        hideCreateView: function() {
            var self = this;
        },
        
        
        /** Matches pagination
        */
        
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
        
        
        /** Views updating
        */
        
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
            
            self.updateBalance();
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
            if (self.match_view_folded) self.foldMatchView(0); // Un peu hack
        },

        
        /** Model
        */
        
        // TODO : balance is a property ?
        // Checks the balance, updates the validation button and the "open balance" line
        updateBalance: function() {
            var self = this;
            var balance = 0; // Debit is +, credit is -
            self.$(".line_open_balance").remove();
            
            // Compute balance
            balance -= self.st_line.amount;
            _.each(self.get("mv_lines_selected"), function(o) {
                balance += o.debit;
                balance -= o.credit;
            });
            
            // Update line_open_balance and button_ok
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
        
        // Loads move lines according to the widget's state and updates the pagers
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
            
            // Update pager controls
            return $.when(deferred_move_lines, deferred_total_move_lines_num).then(function (lines) {
                if (self.get("pager_index") === 0)
                    self.$(".pagerControlLeft").addClass("disabled");
                else
                    self.$(".pagerControlLeft").removeClass("disabled");
                if (self.total_move_lines_num <= ((self.get("pager_index")+1) * self.max_move_lines_displayed))
                    self.$(".pagerControlRight").addClass("disabled");
                else
                    self.$(".pagerControlRight").removeClass("disabled");
            });
        },
        
        // Persist data, notify parent view and terminate widget
        persistAndDestroy: function() {
            var self = this;
            // TODO call
            self.getParent().childValidated(self);
            self.$el.slideUp(300, function(){
                self.destroy();
            });
        },
    });
};