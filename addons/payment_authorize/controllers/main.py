# -*- coding: utf-8 -*-
import os
import sys
import pprint
import jinja2
import logging
import urlparse

from openerp import http
from openerp.http import request

_logger = logging.getLogger(__name__)

if hasattr(sys, 'frozen'):
    # When running on compiled windows binary, we don't have access to package loader.
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
    loader = jinja2.FileSystemLoader(path)
else:
    loader = jinja2.PackageLoader('openerp.addons.payment_authorize', "views")

env = jinja2.Environment(loader=loader, autoescape=True)


class AuthorizeController(http.Controller):
    _return_url = '/payment/authorize/return/'
    _cancel_url = '/payment/authorize/cancel/'

    @http.route([
        '/payment/authorize/return/',
        '/payment/authorize/cancel/',
    ], type='http', auth='public')
    def authorize_form_feedback(self, **post):
        _logger.info('Authorize: entering form_feedback with post data %s', pprint.pformat(post))
        request.env['payment.transaction'].form_feedback(post, 'authorize')
        return_url = post.pop('return_url', '/')
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        #Authorize.Net is expecting a response to the POST sent by their server.
        #This response is in the form of a URL that Authorize.Net will pass on to the
        #client's browser to redirect them to the desired location need javascript.
        return env.get_template("authorize_template.html").render({'return_url': '%s' % urlparse.urljoin(base_url, return_url)})
