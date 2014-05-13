openerp.account_analytic_plans = function(instance) {

var _t = instance.web._t,
    _lt = instance.web._lt;
var QWeb = instance.web.qweb;

instance.web.account.bankStatementReconciliationLine.include({
    
    init: function(parent, context) {
        this._super(parent, context);
        this.create_form_fields.analytic_account.label = "TODO"
    },
    
    start: function() {
        return this._super().then(function() {
        });
    },
});
}