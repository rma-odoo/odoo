# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools.translate import _

# defined for access rules
class sale_order(osv.Model):
    _inherit = "sale.order"

    def _cart_find_product_line(self, cr, uid, ids, product_id=None, line_id=None, context=None, **kwargs):
        line_ids = super(sale_order, self)._cart_find_product_line(cr, uid, ids, product_id, line_id, context=context)
        if line_id:
            return line_ids
        attendee = kwargs.get('attendee', {})
        event_ticket_id = attendee and int(attendee.get('event_ticket_id', False))
        for so in self.browse(cr, uid, ids, context=context):
            if event_ticket_id:
                domain = [('order_id', '=', so.id), ('event_ticket_id', '=', event_ticket_id)]
            else:
                domain = [('id', 'in', line_ids)]
            return self.pool.get('sale.order.line').search(cr, SUPERUSER_ID, domain, context=context)

    def _website_product_id_change(self, cr, uid, ids, order_id, product_id, line_id=None, context=None, **kwargs):
        values = super(sale_order,self)._website_product_id_change(cr, uid, ids, order_id, product_id, line_id=line_id, context=None)
        attendee = kwargs.get('attendee', {})
        event_ticket_id = attendee and int(attendee.get('event_ticket_id', False))
        if not event_ticket_id:
            if line_id:
                line = self.pool.get('sale.order.line').browse(cr, SUPERUSER_ID, line_id, context=context)
                if line.event_ticket_id:
                    event_ticket_id = line.event_ticket_id.id
            else:
                product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
                if product.event_ticket_ids:
                    event_ticket_id = product.event_ticket_ids[0].id

        if event_ticket_id:
            ticket = self.pool.get('event.event.ticket').browse(cr, uid, event_ticket_id, context=context)
            if product_id != ticket.product_id.id:
                raise osv.except_osv(_('Error!'),_("The ticket doesn't match with this product."))

            values['product_id'] = ticket.product_id.id
            values['event_id'] = ticket.event_id.id
            values['event_ticket_id'] = ticket.id
            values['price_unit'] = ticket.price
            values['name'] = "%s: %s" % (ticket.event_id.name, ticket.name)
            event_attendee_ids = []
            attendee_obj = self.pool.get('sale.order.event.attendee')
            for attendee in attendee.get('attendee_list', []):
                if line_id:
                    attendee_ids = attendee_obj.search(cr, uid, [
                            ('sale_order_line_id', '=', line_id),
                            ('name', '=', attendee.get('name')),
                            ('email', '=', attendee.get('email')),
                            ('phone', '=' ,attendee.get('phone'))
                    ])
                    if attendee_ids:
                        continue
                event_attendee_ids.append((0, 0, {'name': attendee.get('name'), 'email': attendee.get('email'), 'phone': attendee.get('phone')}))
            values['event_attendee_ids'] = event_attendee_ids

        return values
