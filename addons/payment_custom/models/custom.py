# -*- coding: utf-'8' "-*-"

import logging

from openerp.osv import osv

_logger = logging.getLogger(__name__)


class PaymentAcquirerCustom(osv.Model):
    _inherit = 'payment.acquirer'

    def custom_get_form_action_url(self, cr, uid, id, context=None):
        return '/payment/custom/payment_details'

    def _get_providers(self, cr, uid, context=None):
        providers = super(PaymentAcquirerCustom, self)._get_providers(cr, uid, context=context)
        providers.append(['custom', 'Custom'])
        return providers
