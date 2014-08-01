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
        return super(sale_order, self).create(cr, uid, vals, context=context)

class MailMail(osv.Model):
    _name = 'mail.mail'
    _inherit = ['mail.mail']

    def send_get_mail_body(self, cr, uid, mail, partner=None, context=None):
        'replace url with shorten one'
        body = super(MailMail, self).send_get_mail_body(cr, uid, mail, partner=partner, context=context)
        print "body..................",body
        return body
