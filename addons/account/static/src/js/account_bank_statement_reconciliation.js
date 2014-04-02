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
            
            this.modelBankStatement = new instance.web.Model("account.bank.statement");
            this.modelBankStatementLine = new instance.web.Model("account.bank.statement.line");
            
            this.maxLineDisplayed = 3; // Maximum number of lines to display 
            
            this.statement_id = 1; // TODO Récupérer via context
            this.linesChildrenWidgets = {}; // Widgets instanciated to represent the statement's lines
            this.totalLines; // Used to keep track of progress
            this.lastDisplayedLineNum; // Number of the last displayed line ; used to fetch its successor
            this.resolvedLines = 0; // idem
            
            this.getLinesQuery = this.modelBankStatementLine.query().filter([['statement_id', '=', this.statement_id]]);
        },
        
        start: function() {
            this._super();
            var self = this;
            var display = this.display_line.bind(this);
            
            // Load from DB : statement infos, number of lines and a first batch of lines
            var deferredStatement = this.modelBankStatement
                .query(["name"])
                .filter([['id', '=', self.statement_id]])
                .first()
                .then(function(statementName){
                    // TODO Juste besoin pour QWeb.render ; quelle portée lexicale pour ne pas encombrer this ?
                    self.statementName = statementName.name;
                });
            var deferredLinesNumber = this.getLinesQuery
                .count()
                .then(function (recordsNum) {
                    self.totalLines = recordsNum;
                });
            var deferredLines = this.getLinesQuery
                .limit(self.maxLineDisplayed)
                .all()
                .then(function (records) {
                    _(records).each(display);
                    self.lastDisplayedLineNum = records.length;
                });
            
            // When queries are done, render template
            return $.when(deferredStatement, deferredLinesNumber, deferredLines)
                .then(function(){
                    self.$el.prepend(QWeb.render("bankStatementReconciliation", {statementName: self.statementName, totalLines: self.totalLines}));
                    // TODO Instancier widget progressbar
                });
        },
        
        display_line: function(line) {
            // TODO BOF
            this.linesChildrenWidgets[line.id] = new instance.web.account.bankStatementReconciliationLine(this, {line: line});
            this.linesChildrenWidgets[line.id].appendTo(this.$el);
        },
        
        childValidated: function(child) {
            var self = this;
            var display = this.display_line.bind(this);
            
            self.resolvedLines++;
            self.updateProgressbar();
            
            // Display new line if there are left ; say goobye if the work is done
            if (self.lastDisplayedLineNum < self.totalLines) {
                this.getLinesQuery
                    .offset(self.lastDisplayedLineNum)
                    .limit(self.lastDisplayedLineNum + 1)
                    .first()
                    .then(function (record) {
                        display(record);
                        self.lastDisplayedLineNum++;
                    });
            } else if (self.resolvedLines === self.totalLines) {
                self.$el.append("<br/><br/><center><button class='button_ok'>Success !</button></center>");
                self.$(".button_ok").click(function(){
                    $("body").append("<div style='position: fixed; top: 0;'><div style='margin-left: -1000px; font-weight: bold; font-size: 35em; -webkit-text-stroke: 10px #fff;'>Bye !</div></div>");
                    $("body").animate({padding: 3000}, 1000);
                });
            }
        },
        
        updateProgressbar: function() {
            var self = this;
            var progBar = this.$(".globalProgress");
            progBar.attr("value", self.resolvedLines);
            progBar.text((self.resolvedLines / this.totalLines) + "%");
        },
    });
    
    instance.web.account.bankStatementReconciliationLine = instance.web.Widget.extend({
        template: 'bankStatementReconciliationLine',
        
        events: {
            "click .button_ok": "persistAndDestroy",
        },
        
        init: function(parent, context) {
            this._super(parent);
            this.modelMoveLine = new instance.web.Model("account.move.line");
            this.line = context.line; // statement line
            this.moveLines; // corresponding move lines
            this.moveLinesSelected; // selected as counterparts
            this.moveLinesHidden; // hidden by the filter feature
            this.pagerIndex; //
        },
        
        start: function() {
            this._super();
            var self = this;
            
            // TODO : not working
            this.on("change:pagerIndex", this, this.applyPager);
            
            var deferredMoveLines = this.modelMoveLine
                .query(["id", "name", "ref", "account_id", "date_maturity", "date", "credit", "debit", "period_id", "journal_id"])
                .filter([['partner_id', '=', self.line.partner_id[0]], ['reconcile_id', '=', false]])
                .all()
                .then(function(records){
                    console.log(records);
                    
                    self.moveLines = records;
                    self.pagerIndex = 0;
                    self.applyPager(); // TODO : RM
                });
            
            this.$(".line_info_button").popover({
                'placement': 'left',
                'container': 'body',
                'html': true,
                'trigger': 'hover',
                'animation': false,
                'toggle': 'popover',
            });
            
            return deferredMoveLines;
        },
        
        // Persist data, notify parent view and terminate widget
        persistAndDestroy: function() {
            var self = this;
            // requests / calls
            this.getParent().childValidated(this);
            this.$el.slideUp(300, function(){
                self.destroy();
            });
        },
        
        // Empties the matching table and populates it
        applyPager: function() {
            var self = this;
            var table = this.$(".match table");
            table.empty();
            _.each(self.moveLines.slice(self.pagerIndex*10, (self.pagerIndex+1)*10), function(item) {
                table.append(QWeb.render("bankStatementReconciliationMoveLine", {line: item}));
            });
        },
        
        // Checks the balance, updates the validation button and the "open balance" line
        updateBalance: function() {
            var debitMissing = 0;
            $(this.find(".accounting_view .ligne_balance_proposition")).remove();
            $.each(this.find(".accounting_view td:nth-child(5)"), function(index, champ){
                var amount = parseInt($(champ).text());
                if (!isNaN(amount)) { debitMissing -= amount; }
            });
            $.each(this.find(".accounting_view td:nth-child(6)"), function(index, champ){
                var amount = parseInt($(champ).text());
                if (!isNaN(amount)) { debitMissing += amount; }
            });
            if (debitMissing === 0 && !(this.hasClass("no_partner"))) {
                this.find(".button_ok").removeClass("button_default");
                this.find(".button_ok").text("OK");
                this.find(".add_line").hide();
            } else {
                this.find(".button_ok").addClass("button_default");
                this.find(".button_ok").text("Keep open");
                var ligneBalanceProposition = $('<tr class="ligne_balance_proposition"><td><span class="glyphicon glyphicon-play"></span></td><td>401000</td><td></td><td>Open balance</td><td>'+(debitMissing>0?debitMissing+".00":"")+'</td><td>'+(debitMissing<0?Math.abs(debitMissing)+".00":"")+'</td><td></td></tr>');
                ligneBalanceProposition.bindLineBalanceProposition();
                $(this).find(".accounting_view tbody").append(ligneBalanceProposition);
            }
        },
    });
};


/*
Asynchronous functions (functions which call session.rpc directly or indirectly at the very least) must return deferreds, so that callers of overriders can correctly synchronize with them.
*/



/* static/src/js/first_module.js
openerp.web_example = function (instance) {
    instance.web.client_actions.add('example.action', 'instance.web_example.Action');
    instance.web_example.Action = instance.web.Widget.extend({
        template: 'web_example.action',
        events: {
            'click .oe_web_example_start button': 'watch_start',
            'click .oe_web_example_stop button': 'watch_stop'
        },
        init: function () {
            this._super.apply(this, arguments);
            this._start = null;
            this._watch = null;
            this.model = new instance.web.Model('web_example.stopwatch');
        },
        start: function () {
            var display = this.display_record.bind(this);
            return this.model.query()
                .filter([['user_id', '=', instance.session.uid]])
                .all().done(function (records) {
                    _(records).each(display);
                });
        },
        current: function () {
            // Subtracting javascript dates returns the difference in milliseconds
            return new Date() - this._start;
        },
        display_record: function (record) {
            $('<li>')
                .text(this.format_time(record.time))
                .appendTo(this.$('.oe_web_example_saved'));
        },
        format_time: function (time) {
            var h, m, s;
            s = time / 1000;
            m = Math.floor(s / 60);
            s -= 60*m;
            h = Math.floor(m / 60);
            m -= 60*h;
            return _.str.sprintf("%02d:%02d:%02d", h, m, s);
        },
        update_counter: function (time) {
            this.$('.oe_web_example_timer').text(this.format_time(time));
        },
        watch_start: function () {
            this.$el.addClass('oe_web_example_started')
                    .removeClass('oe_web_example_stopped');
            this._start = new Date();
            // Update the UI to the current time
            this.update_counter(this.current());
            // Update the counter at 30 FPS (33ms/frame)
            this._watch = setInterval(function () {
                    this.update_counter(this.current());
                }.bind(this),
                33);
        },
        watch_stop: function () {
            clearInterval(this._watch);
            var time = this.current();
            this.update_counter(time);
            this._start = this._watch = null;
            this.$el.removeClass('oe_web_example_started')
                    .addClass('oe_web_example_stopped');
            this.model.call('create', [{
                user_id: instance.session.uid,
                time: time,
            }]);
        },
        destroy: function () {
            if (this._watch) {
                clearInterval(this._watch);
            }
            this._super();
        }
    });
};
*/




//new instance.web.Model("account_bank_statement").query(["name", "image"])
//    .filter([["categ_id.name", "=", "Pet Toys"]]).limit(5).all().then(function(result) {
//    _.each(result, function(item) {
//        var $item = $(QWeb.render("PetToy", {item: item}));
//        self.$el.append($item);
//        $item.click(function() {
//            self.item_clicked(item);
//        });
//    });
//});
