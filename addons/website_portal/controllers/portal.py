# -*- coding: utf-8 -*-
from openerp import http
from openerp.addons.web.http import request


class portal(http.Controller):
    @http.route('/website_portal/portal', auth='public', website=True)
    def index(self, **kw):
        menu_data = request.registry['ir.ui.menu'].load_menus(request.cr, request.uid, context=request.context)
        model, portal_id = request.registry["ir.model.data"].get_object_reference(request.cr, request.uid, 'portal','portal_menu')
        portal_menu = {}
        for menu in menu_data['children']:
            if menu['id'] == portal_id:
                portal_menu['children'] = [menu]
        if not portal_menu:
            return request.render("portal.empty")
        return request.render("website.portal", qcontext={'menu_data': portal_menu})
