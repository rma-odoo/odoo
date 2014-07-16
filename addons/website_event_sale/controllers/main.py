# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website_event.controllers.main import website_event
from openerp.tools.translate import _


class website_event(website_event):

    def _check_website_event_sale_default_template_status(self):
        super(website_event, self)._check_website_event_sale_default_template_status()
        view_ref = request.registry.get('ir.model.data').get_object_reference(request.cr, request.uid, 'website_event_sale', 'registration_template')[1]
        flag = request.registry.get('ir.ui.view').browse(request.cr, request.uid, view_ref).application
        return flag

    @http.route(['/event/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, event_id, **post):
        cr, uid, context = request.cr, request.uid, request.context
        sale_order = request.website.sale_get_order(force_create=1)
        tickets = website_event._prepare_ticket_json(self, post)
        order_obj = request.registry.get('sale.order')
        ticket_obj = request.registry.get('event.event.ticket')
        for ticket_id, item in tickets.items():
            quantity, attendee_list = item
            ticket = ticket_obj.browse(cr, SUPERUSER_ID, int(ticket_id), context=context)
            order_obj._cart_update(cr, uid, [sale_order.id], product_id=ticket.product_id.id, add_qty=int(quantity), context=dict(context, event_ticket_id=ticket.id, attendee_list=attendee_list))
        return request.redirect("/shop/checkout")

    def _add_event(self, event_name="New Event", context={}, **kwargs):
        try:
            dummy, res_id = request.registry.get('ir.model.data').get_object_reference(request.cr, request.uid, 'event_sale', 'product_product_event')
            context['default_event_ticket_ids'] = [[0,0,{
                'name': _('Subscription'),
                'product_id': res_id,
                'deadline' : False,
                'seats_max': 1000,
                'price': 0,
            }]]
        except ValueError:
            pass
        return super(website_event, self)._add_event(event_name, context, **kwargs)
