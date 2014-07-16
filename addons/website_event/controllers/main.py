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

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict

import werkzeug.urls
from werkzeug.exceptions import NotFound

from openerp import http
from openerp import tools, SUPERUSER_ID
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

class website_event(http.Controller):
    @http.route(['/event', '/event/page/<int:page>'], type='http', auth="public", website=True)
    def events(self, page=1, **searches):
        cr, uid, context = request.cr, request.uid, request.context
        event_obj = request.registry['event.event']
        type_obj = request.registry['event.type']
        country_obj = request.registry['res.country']

        searches.setdefault('date', 'all')
        searches.setdefault('type', 'all')
        searches.setdefault('country', 'all')

        domain_search = {}

        def sdn(date):
            return date.strftime('%Y-%m-%d 23:59:59')
        def sd(date):
            return date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        today = datetime.today()
        dates = [
            ['all', _('Next Events'), [("date_end", ">", sd(today))], 0],
            ['today', _('Today'), [
                ("date_end", ">", sd(today)),
                ("date_begin", "<", sdn(today))],
                0],
            ['week', _('This Week'), [
                ("date_end", ">=", sd(today + relativedelta(days=-today.weekday()))),
                ("date_begin", "<", sdn(today  + relativedelta(days=6-today.weekday())))],
                0],
            ['nextweek', _('Next Week'), [
                ("date_end", ">=", sd(today + relativedelta(days=7-today.weekday()))),
                ("date_begin", "<", sdn(today  + relativedelta(days=13-today.weekday())))],
                0],
            ['month', _('This month'), [
                ("date_end", ">=", sd(today.replace(day=1))),
                ("date_begin", "<", (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00'))],
                0],
            ['nextmonth', _('Next month'), [
                ("date_end", ">=", sd(today.replace(day=1) + relativedelta(months=1))),
                ("date_begin", "<", (today.replace(day=1)  + relativedelta(months=2)).strftime('%Y-%m-%d 00:00:00'))],
                0],
            ['old', _('Old Events'), [
                ("date_end", "<", today.strftime('%Y-%m-%d 00:00:00'))],
                0],
        ]

        # search domains
        current_date = None
        current_type = None
        current_country = None
        for date in dates:
            if searches["date"] == date[0]:
                domain_search["date"] = date[2]
                if date[0] != 'all':
                    current_date = date[1]
        if searches["type"] != 'all':
            current_type = type_obj.browse(cr, uid, int(searches['type']), context=context)
            domain_search["type"] = [("type", "=", int(searches["type"]))]
        if searches["country"] != 'all':
            current_country = country_obj.browse(cr, uid, int(searches['country']), context=context)
            domain_search["country"] = [("country_id", "=", int(searches["country"]))]

        def dom_without(without):
            domain = [('state', "in", ['draft','confirm','done'])]
            for key, search in domain_search.items():
                if key != without:
                    domain += search
            return domain

        # count by domains without self search
        for date in dates:
            if date[0] <> 'old':
                date[3] = event_obj.search(
                    request.cr, request.uid, dom_without('date') + date[2],
                    count=True, context=request.context)

        domain = dom_without('type')
        types = event_obj.read_group(
            request.cr, request.uid, domain, ["id", "type"], groupby="type",
            orderby="type", context=request.context)
        type_count = event_obj.search(request.cr, request.uid, domain,
                                      count=True, context=request.context)
        types.insert(0, {
            'type_count': type_count,
            'type': ("all", _("All Categories"))
        })

        domain = dom_without('country')
        countries = event_obj.read_group(
            request.cr, request.uid, domain, ["id", "country_id"],
            groupby="country_id", orderby="country_id", context=request.context)
        country_id_count = event_obj.search(request.cr, request.uid, domain,
                                            count=True, context=request.context)
        countries.insert(0, {
            'country_id_count': country_id_count,
            'country_id': ("all", _("All Countries"))
        })

        step = 10  # Number of events per page
        event_count = event_obj.search(
            request.cr, request.uid, dom_without("none"), count=True,
            context=request.context)
        pager = request.website.pager(url="/event", total=event_count, page=page, step=step, scope=5)

        order = 'website_published desc, date_begin'
        if searches.get('date','all') == 'old':
            order = 'website_published desc, date_begin desc'
        obj_ids = event_obj.search(
            request.cr, request.uid, dom_without("none"), limit=step,
            offset=pager['offset'], order=order, context=request.context)
        events_ids = event_obj.browse(request.cr, request.uid, obj_ids,
                                      context=request.context)

        values = {
            'current_date': current_date,
            'current_country': current_country,
            'current_type': current_type,
            'event_ids': events_ids,
            'dates': dates,
            'types': types,
            'countries': countries,
            'pager': pager,
            'searches': searches,
            'search_path': "?%s" % werkzeug.url_encode(searches),
        }

        return request.website.render("website_event.index", values)

    @http.route(['/event/<model("event.event"):event>/page/<path:page>'], type='http', auth="public", website=True)
    def event_page(self, event, page, **post):
        values = {
            'event': event,
            'main_object': event
        }

        if '.' not in page:
            page = 'website_event.%s' % page

        try:
            request.website.get_template(page)
        except ValueError, e:
            # page not found
            raise NotFound

        return request.website.render(page, values)

    @http.route(['/event/<model("event.event"):event>'], type='http', auth="public", website=True)
    def event(self, event, **post):
        if event.menu_id and event.menu_id.child_id:
            target_url = event.menu_id.child_id[0].url
        else:
            target_url = '/event/%s/register' % str(event.id)
        if post.get('enable_editor') == '1':
            target_url += '?enable_editor=1'
        return request.redirect(target_url);

    @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def event_register(self, event, **post):
        values = {
            'event': event,
            'main_object': event,
            'range': range,
        }
        return request.website.render("website_event.event_description_full", values)

    @http.route('/event/add_event', type='http', auth="user", methods=['POST'], website=True)
    def add_event(self, event_name="New Event", **kwargs):
        return self._add_event(event_name, request.context, **kwargs)

    def _add_event(self, event_name=None, context={}, **kwargs):
        if not event_name:
            event_name = _("New Event")
        Event = request.registry.get('event.event')
        date_begin = datetime.today() + timedelta(days=(14))
        vals = {
            'name': event_name,
            'date_begin': date_begin.strftime('%Y-%m-%d'),
            'date_end': (date_begin + timedelta(days=(1))).strftime('%Y-%m-%d'),
        }
        event_id = Event.create(request.cr, request.uid, vals, context=context)
        event = Event.browse(request.cr, request.uid, event_id, context=context)
        return request.redirect("/event/%s/register?enable_editor=1" % slug(event))

    def get_formated_date(self, event):
        start_date = datetime.strptime(event.date_begin, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
        end_date = datetime.strptime(event.date_end, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
        return ('%s %s%s') % (start_date.strftime("%b"), start_date.strftime("%e"), (end_date != start_date and ("-"+end_date.strftime("%e")) or ""))
    
    @http.route('/event/get_country_event_list', type='http', auth='public', website=True)
    def get_country_events(self ,**post):
        cr, uid, context, event_ids = request.cr, request.uid, request.context,[]
        country_obj = request.registry['res.country']
        event_obj = request.registry['event.event']
        country_code = request.session['geoip'].get('country_code')
        result = {'events':[],'country':False}
        if country_code:
            country_ids = country_obj.search(cr, uid, [('code', '=', country_code)], context=context)
            event_ids = event_obj.search(cr, uid, ['|', ('address_id', '=', None),('country_id.code', '=', country_code),('date_begin','>=', time.strftime('%Y-%m-%d 00:00:00')),('state', '=', 'confirm')], order="date_begin", context=context)
        if not event_ids:
            event_ids = event_obj.search(cr, uid, [('date_begin','>=', time.strftime('%Y-%m-%d 00:00:00')),('state', '=', 'confirm')], order="date_begin", context=context)
        for event in event_obj.browse(cr, uid, event_ids, context=context)[:6]:
            if country_code and event.country_id.code == country_code:
                result['country'] = country_obj.browse(cr, uid, country_ids[0], context=context)
            result['events'].append({
                 "date": self.get_formated_date(event),
                 "event": event,
                 "url": event.website_url})
        return request.website.render("website_event.country_events_list",result)

    def _prepare_ticket_json(self, post):
        '''
            returns the data {'ticket_id': ('quantity', [{attendee data}, {attendee data}, ...])}
            For eg.:
                post = {'phone-5-1-2': u'919898989898', 'email-5-1-2': u'vipattende1@eventoptenerp.com', 'event_ticket_id-4-1-1': u'4', 'name-4-1-1': u'StandardAttendee1', 'email-5-2-2': u'vipattende2@eventoptenerp.com', 'phone-4-1-1': u'919898989898', 'name-5-1-2': u'VIPAttendee1', 'event_ticket_id-5-2-2': u'5', 'name-5-2-2': u'VIPAttendee2', 'phone-5-2-2': u'919898989898', 'email-4-1-1': u'standardattende1@eventoptenerp.com', 'event_ticket_id-5-1-2': u'5'}
                return {'5': ('2', [{'phone': u'919898989898', 'email': u'vipattende1@eventoptenerp.com', 'id': '1', 'event_ticket_id': u'5', 'name': u'VIPAttendee1'}, {'email': u'vipattende2@eventoptenerp.com', 'phone': u'919898989898', 'id': '2', 'event_ticket_id': u'5', 'name': u'VIPAttendee2'}]), '4': ('1', [{'phone': u'919898989898', 'email': u'standardattende1@eventoptenerp.com', 'id': '1', 'event_ticket_id': u'4', 'name': u'StandardAttendee1'}])}
        '''
        tickets = {}
        for key in post:
            field_name, ticket_id, sequence, qty = tuple(key.split('-'))
            if ticket_id not in tickets:
                tickets[ticket_id] = (qty, [])
            attendee_list = tickets[ticket_id][1]
            if not attendee_list:
                attendee = { 'id': sequence }
                attendee_list.append(attendee)
            flag = False
            for attendee in attendee_list:
                if attendee['id'] == sequence:
                    flag = True
                    attendee[field_name] = post[key]
            if not flag:
                attendee = { 'id': sequence, field_name: post[key] }
                attendee_list.append(attendee)
            tickets[ticket_id]= (qty, attendee_list)
        return tickets

    def _check_website_event_sale_default_template_status(self):
        '''
            For checking the status of 'event_attendee_registration' template enabled/disabled. Kept by default disabled bcz if module website_event_sale is not installed than take it as disabled.
        '''
        return 'disabled'

    @http.route(['/event/generate/attendeeform'], type='json', auth="public", methods=['POST'], website=True)
    def attendee_form(self, event_id, **post):
        sale = False
        for key, value in post['post'].items():
            quantity = int(value or "0")
            if not quantity:
                continue
            sale = True
        if not sale:
            return request.redirect("/event/%s" % event_id)
        flag = self._check_website_event_sale_default_template_status()
        return request.website._render("website_event.event_attendee_registration", {
                'post': OrderedDict(sorted(post['post'].items())),
                'event_id': event_id,
                'flag': flag,
                })

    @http.route(['/event/register/attendee'], type='http', auth="public", methods=['POST'], website=True)
    def register_attendee(self, event_id, **post):
        cr, uid, context = request.cr, request.uid, request.context
        attendees_data = []
        attendee_obj = request.registry.get('event.registration')
        tickets = self._prepare_ticket_json(post)
        for ticket_id, item in tickets.items():
            quantity, attendee_list = item
            for attendee in attendee_list:
                attendee['event_id'] = event_id
                attendee_id = attendee_obj.create(cr, SUPERUSER_ID, attendee, context=context)
                attendees_data.append(attendee_obj.browse(cr, uid, attendee_id, context=context))
            return request.website.render("website_event.registration_complete", {
                'uid': uid,
                'attendees': attendees_data,
                'event': request.registry.get('event.event').browse(cr, uid, int(event_id), context=context),
            })
