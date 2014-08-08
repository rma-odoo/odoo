from openerp.addons.web import http
from openerp.tools.translate import _
from openerp.http import request
from openerp import SUPERUSER_ID
import datetime
import werkzeug

class Website_Url(http.Controller):
    @http.route('/r/<string:code>' ,type='http', auth="none", website=True)
    def full_url_redirect(self, code, **post):
        record = request.registry.get('website.alias').search_read(request.cr, SUPERUSER_ID, [('code', '=', code)], ['url'], limit=1, context= request.context)
        rec = record and record[0] or False
        if rec:
            country_id = request.registry.get('res.country').search(request.cr, SUPERUSER_ID, [('code','=',request.session.geoip.get('country_code'))])
            vals = {
                    'alias_id':rec.get('id'),
                    'create_date':datetime.datetime.now().date(),
                    'ip':request.httprequest.remote_addr,
                    'country_id': country_id and country_id[0] or False
                    }
            request.registry.get('website.alias.click').create(request.cr, SUPERUSER_ID, vals, context=request.context)
            print "reccccccccccccc",rec.get('url')
            return werkzeug.utils.redirect(rec.get('url'))

