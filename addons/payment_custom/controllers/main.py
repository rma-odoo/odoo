# -*- coding: utf-8 -*-
import logging

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class CustomController(http.Controller):

    @http.route([
        '/payment/custom/payment_details',
    ], type='http', auth='public', website=True)
    def custom_payment_details(self, **kwargs):
        if not request.website.sale_get_order():
            return request.redirect('/shop')

        values = {}
        values.update(kwargs=kwargs.items())
        return request.render('payment_custom.payment_details', values)

    def update_transaction(self, request, tx_id, values):
        return request.registry['payment.transaction'].write(request.cr, SUPERUSER_ID, tx_id, values, context=request.context)

    @http.route([
        '/payment/custom/feedback',
    ], type='http', auth='public', website=True)
    def custom_payment_feedback(self, **kwargs):
        values = {}

        return_url = kwargs.pop('return_url', '/shop/payment/validate')

        for field_name, field_value in kwargs.items():
            if field_name.startswith('x_') and field_name in request.registry['payment.transaction']._all_columns:
                values[field_name] = field_value

        tx = request.website.sale_get_transaction()
        if not tx:
            return request.redirect('/shop')

        self.update_transaction(request, tx.id, values)

        return request.redirect(return_url)
