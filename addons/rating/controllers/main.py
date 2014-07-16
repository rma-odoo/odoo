# -*- coding: utf-8 -*-

import werkzeug
from openerp.addons.web.http import request
from openerp.addons.web.controllers.main import login_redirect
from openerp.addons.web import http
from openerp.tools.translate import _

class Rating(http.Controller):

    @http.route('/rating/<model>/<int:id>/<state>', type='http', auth="public")
    def rating(self, model, id ,action=None, state=None, url=None, **post):
        state_img = {'great': "<img src='rating/static/src/img/great.png'/>", 'okay': "<img src='rating/static/src/img/okay.png'/>", 'bad': "<img src='rating/static/src/img/bad.png'/>"}
        cr, uid, context = request.cr, request.uid, request.context
        if not request.session.uid:
            return login_redirect()
        partner_id = False
        rating = request.registry['rating.rating']
        rating_ids = rating.search(cr, uid, [('res_model','=',model),('res_id', '=', id),('user_id', '=', uid)], context=context)
        Model = request.registry[model]
        partner = Model.browse(cr, uid, id, context=context).partner_id
        msg = _("Customer rated it ")
        if partner and partner.name:
            msg = "%s %s " % (partner.name, _(" rated it "))
            partner_id = partner.id
        if rating_ids:
            rating.write(cr, uid, rating_ids, {'state': state, 'customer_id': partner_id}, context=context)
        else:
            rating.create(cr, uid,  {'res_model': model, 'state':state, 'res_id': id, 'user_id': uid, 'customer_id': partner_id}, context=context)
        Model.write(cr, uid , [id] , {'is_rated': True})
        Model.message_post(cr, uid, [id], body= msg + state_img[state], context=context)
        return werkzeug.utils.redirect(url and str(url) or '/web#model=%s&id=%s&view_type=form' % (model , id))
