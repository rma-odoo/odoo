
from datetime import datetime, date, timedelta
from openerp.osv import fields, osv
from dateutil.relativedelta import relativedelta

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def _prepare_where_clause_dashboard(self, cr, uid, journal_id, context=None):
        """
            Returns a string for database query.

            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a string for database query to get data for related journal from account invoice.
        """
        if context is None:
            context = {}
        company_id = self.pool['account.journal'].browse(cr, uid, journal_id, context=context).company_id.id
        fiscalyear_id = self.pool['account.journal'].find_fiscalyear(cr, uid, company_id, context=context)
        where_clause = "journal_id = %s AND company_id = %s" % (journal_id, company_id)
        
        if fiscalyear_id:
            where_clause += " AND period_id in \
                            (SELECT account_period.id \
                            FROM account_period \
                            WHERE fiscalyear_id in (%s))" % ','.join(map(str, filter(None, fiscalyear_id)))
        return where_clause

    def _get_remaining_payment_stats(self, cr, uid, journal_id, context=None):
        """
            Returns a dictionary containing overdue_invoice_amount, overdue_invoice_amount_month.
            result format: {
                'overdue_invoice_amount':overdue_amount_today,
                'overdue_invoice_amount_month':overdue_amount_month,
                }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of overdue_invoice_amount,overdue_invoice_amount_month and todo_payment_amount for given journal_id.
        """
        where_clause = self._prepare_where_clause_dashboard(cr, uid, journal_id, context=context)
        cr.execute("SELECT date_due, sum(residual)\
                    FROM account_invoice\
                    WHERE %s\
                    AND state = 'open'\
                    GROUP BY date_due" % where_clause)
        residual_values = cr.fetchall()
        todo_payment_amount = overdue_amount_today = overdue_amount_month = 0

        overdue_month_end_date = date.today() + relativedelta(day=1, months=+1, days=-1)
        for date_due, overdue_invoice_amount in residual_values:
            todo_payment_amount +=  overdue_invoice_amount
            due_date = datetime.strptime(date_due,"%Y-%m-%d").date()
            if due_date <= date.today():
                overdue_amount_today += overdue_invoice_amount
            if due_date <= overdue_month_end_date:
                overdue_amount_month += overdue_invoice_amount
        res = {
            'overdue_invoice_amount' : overdue_amount_today,
            'overdue_invoice_amount_month': overdue_amount_month,
            'todo_payment_amount': todo_payment_amount
        }
        return res

    def get_stats(self, cr, uid, journal_id, context=None):
        """
            Returns a dictionary containing draft_invoice_amount, open_invoice_amount.
            result format: {
                'draft_invoice_amount':amount_total,
                'open_invoice_amount':amount_total,
                }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of draft_invoice_amount,open_invoice_amount and paid_invoice_amount for given journal_id.
        """
        where_clause = self._prepare_where_clause_dashboard(cr, uid, journal_id, context=context)
        # query will return sum for all open and paid invoice based on period id
        cr.execute("SELECT state, sum(amount_total)\
                    FROM account_invoice\
                    WHERE %s\
                    GROUP BY state" % (where_clause))
        invoice_stats = cr.fetchall()
        # query will return sum of all draft invoices which has no period_id
        cr.execute("SELECT sum(amount_total)\
                    FROM account_invoice\
                    WHERE state in ('draft', 'proforma', 'proforma2')\
                    AND journal_id = %s\
                    GROUP BY state" % (journal_id) )
        res = {}
        for amount in cr.fetchall():
            res['draft_invoice_amount'] = amount
        for state, amount_total in invoice_stats:
            if state == 'open':   
                res['open_invoice_amount'] = amount_total
            elif state == 'paid':
                res['paid_invoice_amount'] = amount_total
        remaining_payment_stats = self._get_remaining_payment_stats(cr, uid, journal_id, context=context)
        res.update(remaining_payment_stats)
        return res

class account_journal(osv.osv):
    _inherit = "account.journal"

    def find_fiscalyear(self, cr, uid, company_id, context=None):
        """
            Returns a list containing fiscalyear_id.
            result format: [1]

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param company_id: id of a res.company objects
            @param context: context arguments, like lang, time zone
            @return: Returns a list of fiscalyear_id.
        """
        if context is None:
            context = {}
        fiscalyear_obj = self.pool['account.fiscalyear']
        if context.get('current_year'):
            dt = fields.date.context_today(self,cr,uid,context=context)
            fiscalyear_id = fiscalyear_obj.search(cr, uid, 
                                                    [('date_start', '<=' ,dt),
                                                    ('date_stop', '>=', dt),
                                                    ('company_id', '=', company_id)],
                                                    context=context)
        else:
            fiscalyear_id = fiscalyear_obj.search(cr, uid, [], context=context)
        if not fiscalyear_id:
            fiscalyear_id = [self.pool['account.fiscalyear'].find(cr, uid, context=context)]
        return fiscalyear_id

    def _kanban_dashboard(self, cr, uid, ids, name, arg, context=None):
        """
            Returns a dictionary containing todo_payment_amount, credit_account_name,etc.
            result format: {
                'todo_payment_amount':18.98,
                'credit_account_name':Product Sales - (test),
                }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param ids: ids of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of todo_payment_amount,credit_account_name,etc for journal.
        """
        res = {}
        for journal_id in ids:
            res[journal_id] = self.get_journal_dashboard_datas(cr, uid, journal_id, context=context)
        return res

    def _kanban_graph(self, cr, uid, ids, name, arg, context=None):
        """
            Returns a dictionary containing data for graph like as graph type,values of x and y,etc.
            result format: {
                'bar':True,
                'values': [{'y': 0, 'x': 'Jan'}],
                'key': u'Fiscal Year X 2014',
                }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param ids: ids of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of graph type,values of x and y,key,etc for journal.
        """
        res = {}
        for journal_id in ids:
            res[journal_id] = self._prepare_graph_data(cr, uid, journal_id, context=context)
        return res

    _columns = {
        'kanban_dashboard':fields.function(_kanban_dashboard, type="text"),
        'kanban_graph':fields.function(_kanban_graph, type="text"),
    }

    def get_journal_dashboard_datas(self, cr, uid, journal_id, context=None):
        """
            Returns a dictionary containing todo_payment_amount, credit_account_name,etc.
            result format: {
                'todo_payment_amount':18.98,
                'credit_account_name':Product Sales - (test),
                }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of todo_payment_amount,credit_account_name,etc for journal.
        """
        journal = self.browse(cr, uid, journal_id ,context=context)
        balance, date = self._get_last_statement(cr, uid, journal_id, context=context)
        values = self.pool['account.invoice'].get_stats(cr, uid, journal_id, context=context)
        currency_symbol = journal.company_id.currency_id.symbol
        if journal.currency:
            currency_symbol = journal.currency.symbol
        fiscalyear_id = self.find_fiscalyear(cr, uid, journal.company_id.id, context=context)
        total_reconcile_amount = self.pool['account.move.line'].search(cr, uid, 
                                                        [('journal_id', '=', journal_id),
                                                        ('period_id.fiscalyear_id', 'in', fiscalyear_id),
                                                        ('reconcile_partial_id','!=',False)], count=True, context=context)

        values.update({
            'currency_symbol' : currency_symbol,
            'last_statement_amount' : balance,
            'last_statement_date' : date,
            'total_reconcile_amount' : total_reconcile_amount,
            'credit_account_name': journal.default_credit_account_id.name,
            'credit_account_balance' : journal.default_credit_account_id.balance,
        })
        return values

    def _get_last_statement(self, cr, uid, journal_id, context=None):
        """
            Returns a tuple containing amount and date of last_statement.
            result format: (1100.0, '06/13/2014')

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a tuple of amount and date of last_statement for can and bank type journal.
        """
        balance = False
        date = False
        statement_obj = self.pool['account.bank.statement']
        date_format = self.pool['res.lang'].search_read(cr, uid, 
                                                        [('code','=', context.get('lang', 'en_US'))],
                                                        ['date_format'], context=context)[0]['date_format']
        statement_ids = statement_obj.search(cr, uid, 
                                                    [('journal_id', '=', journal_id)],
                                                    order='create_date desc', limit=1, context=context)
        #Get last bank statement amount and date.
        if statement_ids:
            statement = statement_obj.browse(cr, uid, statement_ids, context=context)[0]
            if statement.journal_id.type == 'cash':
                balance = statement.balance_end
            elif statement.journal_id.type == 'bank':
                balance = statement.balance_end_real
            date = datetime.strptime(str(statement.date), '%Y-%m-%d').date().strftime(date_format)
        return (balance , date)

    def _prepare_graph_data(self, cr, uid, journal_id, context=None):
        """
            Returns a dictionary values of x,y coordinate,key,etc.
            result format: {
                            'bar': True,
                            'values': [{'y': 0, 'x': 'Jan'}, {'y': 0, 'x': 'Feb'}, {'y': 0, 'x': 'Mar'}, etc], 
                            'key': u'Fiscal Year X 2014'
                            }

            @param cr: A database cursor
            @param user: ID of the user currently logged in
            @param journal_id: id of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of x,y coordinate,key,etc for given journal_id.
        """
        res = False
        journal = self.browse(cr, uid, journal_id, context=context)
        #Prepare data to show graph in kanban of journals which will be called from the _kanban_graph method
        if journal.type in ['general','situation']:
            return res
        elif journal.type in ['cash','bank']:
            res = self._get_moves_per_day(cr, uid, journal, context=context)
        else:
            res = self._get_moves_per_month(cr, uid, journal, context=context)
        return res

    def _get_moves_per_month(self, cr, uid, journal, context=None):
        """
            Returns a dictionary containing value of x,y coordinate and key.
            result format: {
                                'bar':True,
                                'values': [{'y': 0, 'x': 'Jan'}],
                                'key': 'Fiscal Year X 2014',
                            }

            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param journal: record of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of of x,y coordinate and key for related journal like as cash and bank.
        """
        total = {}
        fiscalyear_obj = self.pool['account.fiscalyear']
        fiscalyear_id = self.find_fiscalyear(cr, uid, journal.company_id.id, context=context)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if journal.type=='sale':
            state = ['posted'] 
        else:
           state = ['draft','posted']
        """
            Get amount of moves related to the particular journals per month
            left join on account_move if we want only posted entries then we can use.
            query will return sum of line.debit and month for related sale,purchase,sale_refund,purchase_refund type journal based on period id
        """
        cr.execute("SELECT to_char(line.date, 'MM') as month, SUM(line.debit) as amount\
                    FROM account_move_line AS line LEFT JOIN account_move AS move ON line.move_id=move.id\
                    WHERE line.journal_id = %s AND line.period_id in (SELECT account_period.id from account_period WHERE fiscalyear_id in %s) \
                    AND move.state in %s\
                    GROUP BY to_char(line.date, 'MM') \
                    ORDER BY to_char(line.date, 'MM')", (journal.id, tuple(fiscalyear_id), tuple(state)))
        values = []
        for month, amount in cr.fetchall():
            values.append({
                'x': months[int(month) - 1],
                'y': amount
            })
        key_name = "Fiscal Year X "
        lst = []
        for fis_record in fiscalyear_obj.browse(cr, uid, fiscalyear_id, context=context):
            key_name += str(datetime.strptime(fis_record.date_start , '%Y-%m-%d').year)
            lst.append(fiscalyear_id)
            if len(lst) != len(fiscalyear_id) :
                key_name += ','
        data = {
            'values': [],
            'bar': True,
            'key': key_name
        }
        for month in months:
            amount = 0
            for value in values:
                if month == value['x']:
                    amount = value['y']
            data['values'].append({'x': month, 'y': amount})
        return data

    def _get_moves_per_day(self, cr, uid, journal, context=None):
        """
            Returns a dictionary containing value of x,y coordinate and key.
            result format: {
                                'values': [{'y': 200.0, 'x': '06/12/2014'}],
                                'key': 'Total'
                            }

            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param journal: record of a account.journal objects
            @param context: context arguments, like lang, time zone
            @return: Returns a dictionary of of x,y coordinate and key for related journal like as cash and bank.
        """
        data = {'values': [], 'key': 'Total'}
        date_format = self.pool['res.lang'].search_read(cr, uid,
                                                        [('code', '=', context.get('lang', 'en_US'))],
                                                        ['date_format'], context=context)[0]['date_format']
        move_date = date.today()-timedelta(days=14)
        fiscalyear_id = self.find_fiscalyear(cr, uid, journal.company_id.id, context=context)
        """
            Get total transactions per day for related journals
            left join on account_move if we want only posted entries then we can use.
            query will return sum of line.debit and line.date for related cash and bank type journal based on period id
        """
        cr.execute("SELECT SUM(line.debit), line.date\
                         FROM account_move_line AS line LEFT JOIN account_move AS move ON line.move_id=move.id\
                         WHERE line.journal_id = %s AND line.period_id in (SELECT account_period.id from account_period WHERE account_period.fiscalyear_id in %s) \
                         AND line.date >= %s\
                         GROUP BY line.date \
                         ORDER BY line.date",(journal.id, tuple(fiscalyear_id), move_date))
        for value in cr.dictfetchall():
            data['values'].append({
                'x': datetime.strptime(str(value['date']), '%Y-%m-%d').date().strftime(date_format),
                'y': value['sum']
            })
        if not data['values']:
            data['values'].append({
                                    'x': datetime.strptime(str(date.today()), '%Y-%m-%d').date().strftime(date_format),
                                    'y': 0
                                })
        return data

    def open_action(self, cr, uid, ids, context=None):
        """return action based on type for related journals"""
        if context is None:
            context = {}
        ir_model_obj = self.pool['ir.model.data']
        rec = self.browse(cr, uid, ids, context=context)[0]
        if rec.type == 'bank':
            action_name = 'action_bank_statement_tree'
        elif rec.type == 'cash':
            action_name = 'action_view_bank_statement_tree'
        elif rec.type == 'sale':
            action_name = 'action_invoice_tree1'
        elif rec.type == 'purchase':
            action_name = 'action_invoice_tree2'
        elif rec.type == 'sale_refund':
            action_name = 'action_invoice_tree3'
        elif rec.type == 'purchase_refund':
            action_name = 'action_invoice_tree4'
        action_name = context.get('action_name',action_name)
        ctx = context.copy()
        _journal_invoice_type_map = {
                                        'sale': 'out_invoice',
                                        'purchase': 'in_invoice',
                                        'sale_refund': 'out_refund', 
                                        'purchase_refund': 'in_refund', 
                                        'bank': 'bank', 
                                        'cash': 'cash'
                                    }
        invoice_type = _journal_invoice_type_map[rec.type]
        ctx.update({
                        'journal_type': rec.type,
                        'default_journal_id': rec.id,
                        'search_default_journal_id': rec.id,
                        'default_type': invoice_type,
                        'type': invoice_type
                    })
        domain = [('journal_id.type', '=', rec.type),('journal_id', '=', rec.id)]
        model, action_id = ir_model_obj.get_object_reference(cr, uid, 'account', action_name)
        action = self.pool[model].read(cr, uid, action_id, context=context)
        action['context'] = ctx
        action['domain'] = domain
        return action
