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
        values = {}
        values.update(kwargs=kwargs.items())
        return request.render('payment_custom.payment_details', values)

    def update_transaction(self, request, values):
        tx = request.website.sale_get_transaction()
        if not tx:
            return False
        return request.registry['payment.transaction'].write(request.cr, SUPERUSER_ID, tx.id, values, context=request.context)

    @http.route([
        '/payment/custom/feedback',
    ], type='http', auth='public', website=True)
    def custom_payment_feedback(self, **kwargs):
        values = {}

        return_url = kwargs.pop('return_url', '/shop/payment/validate')

        for field_name, field_value in kwargs.items():
            if field_name.startswith('x_') and field_name in request.registry['payment.transaction']._all_columns:
                values[field_name] = field_value

        if not self.update_transaction(request, dict(values, user_id=False)):
            return request.redirect('/shop')

        return request.redirect(return_url)
