import string
import random
from openerp.osv import osv, fields

class website_alias(osv.Model):
    _name = "website.alias"
    _rec_name = 'code'
    
    def count_url(self, cr, uid, ids, name, args, context=None):
        click_obj = self.pool.get('website.alias.click')
        res = {}
        for alais in self.browse(cr, uid, ids, context=context):
            res[alais.id] = len(click_obj.search(cr, uid, [('alias_id', '=', alais.id)], context=context))
        return res
    
    def alias_click(self, cr, uid, ids, context=None):
        for click in self.browse(cr, uid, ids, context=context):
            return self.pool.get('website.alias').search(cr, uid, [('id', '=', click.alias_id.id)], context=context)
        return []
    
    def _get_random_code_string(self, cr, uid, ids, name, arg, context=None):
        res = {}
        def random_string(id):
            size = 3
            while True:
                x = ''.join(random.choice(string.letters + string.digits) for _ in range(size))
                if not x: 
                    size += 1 
                else: 
                     return x + str(id)
        for id in ids:
            res[id]= random_string(id)
        return res

    _columns = {
        'url': fields.char('Full URL', required=True),
        'code': fields.function(_get_random_code_string, string='Short URL Code', type='char', store=True),
        'count': fields.function(count_url,string='Number of Clicks', type='integer',
            store={'website.alias': (lambda self, cr, uid, ids, ctx: ids, ['code','url'], 20),
                   'website.alias.click': (alias_click,['alias_id'],20)
                   }),
    }

    sql_constraints = [
        ('code', 'unique( code )', 'Code must be unique.'),
    ]

class website_alias_click(osv.Model):
    _name = "website.alias.click"
    _rec_name = 'alias_id'
    _columns = {
        'click_date': fields.date('Create Date'),
        'alias_id': fields.many2one('website.alias','Alias'),
        'ip': fields.char('Internet Protocol'),
        'country_id': fields.many2one('res.country','Country')
    }
