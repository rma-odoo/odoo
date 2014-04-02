openerp.account = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.account = instance.web.account || {};

    instance.web.account.bankStatementReconciliationLine = instance.web.Widget.extend({
        className: 'oe_bank_statement_reconciliation_line',
        
        init: function(parent, context) {
            this._super(parent);
            this.line = context.line;
            debugger;
        },
        
        start: function() {
            this._super();
            this.$el.append(QWeb.render("bankStatementReconciliation", {statementName: "kikoo !"}));
            var display = this.display_move.bind(this);
            return this.model.query()
                .filter([['statement_id', '=', this.statement_id]])
                .limit(15)
                .all().then(function (records) {
                    _(records).each(display);
                });
        },
        
        display_move: function(move) {
            var self = this;
            debugger;
        },
    });
}