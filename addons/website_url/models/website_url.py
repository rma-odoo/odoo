from openerp.osv import orm
class website_alias(osv.osv):
    _name = "website.alias"
    __rec_name = 'code'
    _columns = {
        'url': fields.char('Full URL', required=True),
        'code': fields.char('Short URL Code', required=True),
        'mail_stat_id': many2one('mail.mail.statistics'),
        #'count': fields.function('Number of Clicks')
    }
#    _default
#   _constraint

class website_alias_click(osv.osv):
    _name = "website.alias.click"
    __rec_name = 'code'
    _columns = {
        'create_date': fields.date('Create Date'),
        'alias_id': many2one('website.alias'),
        'IP': fields.char('Internet Protocol'),
        'country_id': fields.many2one('res.country')
    }
