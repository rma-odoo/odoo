/* ABOUT
    bankStatementReconciliation is a container for the "single reconciliation" widgets (bankStatementReconciliationLine). The displayed data is retreives from the model as an array of arrays which contains the statement line as first item and an array of move lines as second item. [[st_line, [mv_line, ...]], ...]

    st_line : account.bank.statement.line
    mv_line : account.move.line
*/

/* TODO
    Extraire méthodes de account voucher (load, commit)
    create
    change partner :
        - query pour update statement_line (set partner_id = ...)
        - self.start ? Extraire la méthode loadMoveLines
    i18n
    demo data
    tests
    
    si montant facture > montant st_line : afficher /!\ jaune : hover "partial reconcile ?", clic split (quelle logique des données ?)
    set as state in bank statement action ; get satetment id via domain field ; use openerp widgets
    deselected lines -> tableau à part (et IDs exclus de updateMatches)
*/

/* BUGS
    validate too quick : TypeError: 'undefined' is not an object (evaluating 'self.getParent().childValidated')
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
        
        // preferences of children bankStatementReconciliationLine
        this.max_move_lines_displayed = 5;
        this.animation_speed = 300;
        
        // Only for statistical purposes
        this.lines_resolved_with_ctrl_enter = 0;
        this.time_widget_loaded = Date.now();
    },
    
    start: function() {
        this._super();
        var self = this;
        
        // Inject variable styles
        var style = document.createElement("style");
        style.appendChild(document.createTextNode(""));
        document.head.appendChild(style);
        var css_selector = ".oe_bank_statement_reconciliation_line .toggle_match, .oe_bank_statement_reconciliation_line .toggle_create";
        if(style.sheet.insertRule) {
            style.sheet.insertRule(css_selector + " { -webkit-transition-duration: "+self.animation_speed+"ms; }");
            style.sheet.insertRule(css_selector + " { -moz-transition-duration: "+self.animation_speed+"ms; }");
            style.sheet.insertRule(css_selector + " { -ms-transition-duration: "+self.animation_speed+"ms; }");
            style.sheet.insertRule(css_selector + " { -o-transition-duration: "+self.animation_speed+"ms; }");
            style.sheet.insertRule(css_selector + " { transition-duration: "+self.animation_speed+"ms; }");
        } else {
            style.sheet.addRule(css_selector, "-webkit-transition-duration: "+self.animation_speed+"ms;");
            style.sheet.addRule(css_selector, "-moz-transition-duration: "+self.animation_speed+"ms;");
            style.sheet.addRule(css_selector, "-ms-transition-duration: "+self.animation_speed+"ms;");
            style.sheet.addRule(css_selector, "-o-transition-duration: "+self.animation_speed+"ms;");
            style.sheet.addRule(css_selector, "-webkit-transition-duration: "+self.animation_speed+"ms;");
        }
        
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
            });
                    
        // When queries are done, render template andreconciliation lines
        return $.when(deferred_statement, deferred_lines)
            .then(function(){
                self.$el.prepend(QWeb.render("bank_statement_reconciliation", {statement_name: self.statement_name, total_lines: self.st_lines.length}));
                var reconciliations_to_show = self.st_lines.slice(0, self.max_reconciliations_displayed);
                self.last_displayed_reconciliation_index = reconciliations_to_show.length;
                self.displayReconciliation(reconciliations_to_show.shift(), 'match');
                _(reconciliations_to_show).each(function(o){ self.displayReconciliation(o, 'inactive'); });
            });
    },
    
    // adds fields, prefixed with q_, to the statement line for qweb rendering
    prepareStatementLineForRendering: function(line){
        var self = this;
        line.q_account_num = line.account_id[1].split(' ')[0];
        line.q_amount = line.amount.toFixed(2);
        line.q_currency = "EUR" // TODO : fetch correct value
        line.q_popover = QWeb.render("bank_statement_reconciliation_line_details", {line: line});
    },
    
    keyboardShortcutsHandler: function(e) {
        var self = this;
        if (e.which === 13 && (e.ctrlKey || e.metaKey)) {
            $.each(self.getChildren(), function(i, o){
                self.lines_resolved_with_ctrl_enter++;
                o.persistAndDestroy();
            });
        }
    },
    
    displayReconciliation: function(st_line, mode) {
        var self = this;
        self.prepareStatementLineForRendering(st_line);
        new instance.web.account.bankStatementReconciliationLine(self, {st_line: st_line, mode: mode}).appendTo(self.$(".reconciliation_lines_container"));
    },
    
    childValidated: function(child) {
        var self = this;
        
        self.resolved_lines++;
        self.updateProgressbar();
        
        // Display new line if there are left
        if (self.last_displayed_reconciliation_index < self.st_lines.length) {
            self.displayReconciliation(self.st_lines[self.last_displayed_reconciliation_index++], 'inactive');
        }
        // Puts the first line in match mode
        if (self.resolved_lines !== self.st_lines.length) {
            var first_child = self.getChildren()[0];
            if (first_child.get("mode") === first_child.mode_inactive) {
                first_child.set("mode", first_child.mode_match);
            }
        }
        // Congratulate the user if the work is done
        if (self.resolved_lines === self.st_lines.length) {
            self.displayDoneMessage();
        }
    },
    
    displayDoneMessage: function() {
        var self = this;

        var sec_taken = Math.round((Date.now()-self.time_widget_loaded)/1000);
        var sec_per_item = Math.round(sec_taken/self.resolved_lines);
        var achievements = [];
        
        if (sec_taken/60 >= 1) var time_taken = Math.floor(sec_taken/60) +"' "+ sec_taken%60 +"''";
        else var time_taken = sec_taken%60 +" seconds";
        
        if (sec_per_item < 5) var title = "Whew, that was fast ! <i class='fa fa-trophy congrats_icon'></i>";
        else var title = "Congrats, you're all done ! <i class='fa fa-thumbs-o-up congrats_icon'></i>";
        
        if (self.lines_resolved_with_ctrl_enter === self.resolved_lines)
            achievements.push({
                title: "Efficiency at its finest",
                desc: "Only use the ctrl-enter shortcut to validate reconciliations.",
                icon: "fa-keyboard-o"}
            );
        
        if (sec_per_item < 5)
            achievements.push({
                title: "Fast resolver",
                desc: "Take on average less than 5 seconds to reconcile a transaction.",
                icon: "fa-bolt"}
            );
        
        self.$(".protip").hide();
        self.$(".oe_form_sheet").append(QWeb.render("bank_statement_reconciliation_done_message", {
            title: title,
            time_taken: time_taken,
            sec_per_item: sec_per_item,
            transactions_done: self.resolved_lines,
            done_with_ctrl_enter: self.lines_resolved_with_ctrl_enter,
            achievements: achievements
        }));
        
        // Animate the stuff
        var container = $("<div style='overflow: hidden;' />");
        self.$(".done_message").wrap(container).css("opacity", 0).css("position", "relative").css("left", "-50%");
        self.$(".done_message").animate({opacity: 1, left: 0}, self.animation_speed*2, "easeOutCubic");
        self.$(".done_message").animate({opacity: 1}, self.animation_speed*3, "easeOutCubic");
        
        // Make it interactive
        self.$(".achievement").popover({'placement': 'top', 'container': self.el, 'trigger': 'hover'});
        /*
        dispatch_to_new_action: function() {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "product.product",
                res_id: 1,
                views: [[false, 'form']],
                target: 'current',
                context: {},
            });
        },
        */
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
        "click .line_info_button": function(e){e.stopPropagation();}, // small usability hack
    },
    
    init: function(parent, context) {
        this._super(parent);
        
        this.context = context;
        this.st_line = context.st_line;
        this.max_move_lines_displayed = this.getParent().max_move_lines_displayed;
        this.animation_speed = this.getParent().animation_speed;
        this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
        
        this.total_move_lines_num = undefined; // Used for pagers and "show X more"
        this.filter = "";
        
        this.mode_no_partner = 0;
        this.mode_inactive = 1;
        this.mode_match = 2;
        this.mode_create = 3;
        
        this.q_mode = context.mode; // for QWeb ; the mode is applied through an attribute set on the main table
    },
    
    start: function() {
        this._super();
        var self = this;
        
        // no animation while loading
        var animation_speed = self.animation_speed;
        self.animation_speed = 0;
        
        // binds not covered by the events section
        self.bindPopoverTo(self.$(".line_info_button"));
        
        // Create sub-widgets
        // TODO : render and append a input_manager
        self.renderCreateForm();
        
        // properties
        this.set("balance", undefined); // Debit is +, credit is -
        self.on("change:balance", self, self.balanceChanged);
        
        this.set("mode", undefined);
        self.on("change:mode", self, self.modeChanged);
        this.set("mode", this["mode_"+self.context.mode]);
        
        this.set("pager_index", 0);
        self.on("change:pager_index", self, self.pagerChanged);
        
        this.set("mv_lines", []);
        self.on("change:mv_lines", self, self.mvLinesChanged);
        
        this.set("mv_lines_selected", []);
        self.on("change:mv_lines_selected", self, self.mvLinesSelectedChanged);
        
        this.set("lines_created", []);
        self.on("change:lines_created", self, self.createdLinesChanged);
        
        // load and display
        self.$el.css("opacity", "0");
        return $.when(self.loadResolutionProposition())
            .then(function(){
                return $.when(self.updateMatches());
            }).then(function(){
                self.animation_speed = animation_speed; // all right, there can be animations now
                self.$el.animate({opacity: 1}, this.animation_speed);
            });
    },
    

    /** Utils */
    
    renderCreateForm: function() {
        var self = this;
        
        // field_manager stuff
        var dataset = new instance.web.DataSet(this, "account.account", this.context)
        dataset.arch = {
            attrs: { string: "lol", version: "7.0" },
            children: [],
            tag: "form"
        };
        dataset.ids = [];

        var node = {
            attrs: {
                invisible: "False",
                modifiers: '{"readonly":false}',
                name: "account",
                nolabel: "true"
            },
            children: [],
            tag: "field"
        };
        
        var field_manager = new instance.web.FormView (
            this, dataset, false, {
                initial_mode: 'edit',
                disable_autofocus: false,
                $buttons: $(),
                $pager: $()
        });
        
        field_manager.load_form(dataset);
        
        // fields properties
        field_manager.fields_view.fields = {
            account : {
                context: {},
                domain: [],
                help: "",
                readonly: false,
                relation: "account.account",
                required: true,
                selectable: true,
                states: {},
                string: "Account",
                type: "many2one",
                views: {}
            }
        };
        
        // instantiate fields and append them
        var account_field = new instance.web.form.FieldMany2One(field_manager, node);
        
        account_field.appendTo(self.$(".create_account"));
    },
    
    // adds fields, prefixed with q_, to the move line for qweb rendering
    prepareMoveLineForRendering: function(line){
        var self = this;
        line.q_account_num = line.account_id[1].split(' ')[0];
        line.q_debit = (line.debit === 0 ? "" : line.debit.toFixed(2));
        line.q_credit = (line.credit === 0 ? "" : line.credit.toFixed(2));
        line.q_due_date = (line.date_maturity === false ? line.date : line.date_maturity);
        line.q_amount = (line.q_debit !== "" ? line.q_debit : "") + (line.q_credit !== "" ? "- "+line.q_credit : "");
        line.q_popover = QWeb.render("bank_statement_reconciliation_move_line_details", {line: line});
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
        $row.find('> td').animate({paddingTop: 0, paddingBottom: 0}, speed);
        $row.animate({opacity: 0}, speed/2);
    },
    
    slideDownTableRow: function($row, speed) {
        var self = this;
        speed = (typeof speed !== 'undefined' ? speed : self.animation_speed);
        
        if ($row.context.dataset.suitableforsliding !== "true") {
            $row.find('td').wrapInner('<div />');
            $row.context.dataset.suitableforsliding = "true";
        }
        $row.find('td > div').slideDown(speed);
        $row.find('> td').animate({paddingTop: 1, paddingBottom: 1}, speed); // TODO Warning : duplicate from CSS
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
        var mv_lines_selected = _.filter(self.get("mv_lines_selected"), function(o) { return o.id != line_id; });
        
        self.set("mode", self.mode_match);
        self.set("mv_lines_selected", mv_lines_selected);
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
        self.filter = self.$(".filter").val();
        window.clearTimeout(self.apply_filter_timeout);
        self.apply_filter_timeout = window.setTimeout(self.proxy('updateMatches'), 200);
    },
    
    
    /** Creating */
    
    addLine: function() {
        var self = this;
    },
    
    removeLine: function() {
        var self = this;
    },
    
    
    /** Display */
    
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
            self.set("mode", self.mode_match);
        } else {
            self.set("mode", self.mode_create);
        }
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
        
        // When there is no match to show, hide the view
        if (self.total_move_lines_num === 0 && self.filter === "") {
            self.$(".match").slideUp(self.animation_speed);
        } else if (self.get("mode") === this.mode_match && ! self.$(".match").is(":visible")) {
            self.$(".match").slideDown(self.animation_speed);
        }
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
    
    
    /** Properties changed */
    
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
            self.$(".match").slideUp(self.animation_speed);
            self.$(".create").slideUp(self.animation_speed);
            self.el.dataset.mode = "inactive";
        } else if (self.get("mode") === self.mode_match) {
            self.$(".match").slideDown(self.animation_speed);
            self.$(".create").slideUp(self.animation_speed);
            self.$(".action_pane.match").addClass("active");
            self.el.dataset.mode = "match";
        } else if (self.get("mode") === self.mode_create) {
            self.$(".match").slideUp(self.animation_speed);
            self.$(".create").slideDown(self.animation_speed);
            self.$(".action_pane.create").addClass("active");
            self.el.dataset.mode = "create";
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
    
    
    /** Model */
    
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
                _(lines).each(self.prepareMoveLineForRendering.bind(self));
                self.set("mv_lines_selected", self.get("mv_lines_selected").concat(lines));
            });
    },
    
    // Loads move lines according to the widget's state
    updateMatches: function() {
        var self = this;
        
        var move_lines = {};
        var move_lines_num = 0;
        var offset = self.get("pager_index") * self.max_move_lines_displayed;
        var mv_lines_selected_ids = _.collect(self.get("mv_lines_selected"), function(o){ return o.id; });
        
        // Load move lines
        var deferred_move_lines = self.model_bank_statement_line
            .call("get_move_lines", [self.st_line.id, mv_lines_selected_ids, self.filter, offset, self.max_move_lines_displayed])
            .then(function (lines) {
                move_lines = lines;
            });
        
        // Fetch the number of move lines corresponding to this statement line and this filter
        var deferred_total_move_lines_num = self.model_bank_statement_line
            .call("get_move_lines", [self.st_line.id, mv_lines_selected_ids, self.filter, offset, self.max_move_lines_displayed, true])
            .then(function(num){
                move_lines_num = num;
            });
        
        return $.when(deferred_move_lines, deferred_total_move_lines_num).then(function(){
            self.total_move_lines_num = move_lines_num;
            self.set("mv_lines", move_lines);
            // If pager_index is out of range, set it to display the last page
            if (self.get("pager_index") !== 0 && self.total_move_lines_num <= (self.get("pager_index") * self.max_move_lines_displayed)) {
                self.set("pager_index", Math.ceil(self.total_move_lines_num/self.max_move_lines_displayed)-1);
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
            self.$el.parent().remove();
            var parent = self.getParent();
            $.when(self.destroy()).then(
                parent.childValidated(self)
            );
        });
    },
});
};