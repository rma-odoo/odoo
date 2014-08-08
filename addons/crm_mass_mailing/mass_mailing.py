import re
from openerp.osv import osv, fields

URL_REGEX = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

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

class MassMailing(osv.Model):
    _name = 'mail.mass_mailing'
    _inherit = ['mail.mass_mailing']

    def convert_link(self,cr, uid, body, context=None):
        urls = re.findall(URL_REGEX, body)
        website_alias = self.pool.get('website.alias')
        for long_url in urls:
            shorten_url = website_alias.create_shorten_url(cr, uid, {'url':url}, context=context)
            if shorten_url:body = body.replace(long_url, shorten_url)
        return body
    
    def send_mail(self, cr, uid, ids, context=None):
        for mailing in self.browse(cr, uid, ids, context=context):
            body_html = self.convert_link(cr, uid, mailing.body_html, context=context)
            self.write(cr, uid, mailing.id, {'body_html':body_html}, context=context)
        return super(MassMailing, self).send_mail(cr, uid, ids, context=context)