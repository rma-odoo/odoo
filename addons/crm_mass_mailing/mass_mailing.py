import re
from urlparse import urlparse
from urlparse import urljoin
from openerp.osv import osv, fields
class MassMailingCampaign(osv.Model):
    _name = 'mail.mass_mailing.campaign'
    _inherit = ['mail.mass_mailing.campaign', 'crm.tracking.mixin']
    
    def _get_souce_id(self, cr, uid, context=None):
        souce_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm', 'crm_source_newsletter')
        return souce_id and souce_id[1] or False

    def _get_medium_id(self, cr, uid, context=None):
        medium_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm', 'crm_medium_email')
        return medium_id and medium_id[1] or False

    _defaults = {
            'source_id': lambda self, *args: self._get_souce_id(*args),
            'medium_id' : lambda self, *args: self._get_medium_id(*args),
    }
    def create(self, cr, uid, vals, context=None):
        if vals.get('name'):
            vals['campaign_id'] = self.pool.get('crm.tracking.campaign').create(cr, uid, {'name': vals.get('name')}, context=context)
        return super(MassMailingCampaign, self).create(cr, uid, vals, context=context)

class MailMail(osv.Model):
    _name = 'mail.mail'
    _inherit = ['mail.mail']
    def convert_link(self,cr, uid, body, context=None):
        url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_regex, body)
        website_alias = self.pool.get('website.alias')
        for url in urls:
            index,length = body.index(url),len(url)
            alais_id = website_alias.create(cr, uid, {'url':url}, context=context)
            code = website_alias.browse(cr, uid, alais_id, context=context).code
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))
            track_url = urljoin(domain, '/r/%(code)s' % {'code': code,})
            body = body[:index -1] + track_url + body[index+length+1:]
        print "newwwwwwwwwwwwwwwwww",body
        return body
    def send_get_mail_body(self, cr, uid, mail, partner=None, context=None):
        body = super(MailMail, self).send_get_mail_body(cr, uid, mail, partner=partner, context=context)
        return self.convert_link(cr, uid, body, context)
