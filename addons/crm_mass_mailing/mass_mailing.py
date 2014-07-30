from openerp.osv import osv


class MassMailing(osv.Model):
    _name = 'mail.mass_mailing'
    _inherit = ['mail.mass_mailing', 'crm.tracking.mixin']

    def _get_souce_id(self, cr, uid, context=None):
        souce_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'mass_mailing', 'mass_mail_list_1')
        return souce_id and souce_id[1] or False

    def _get_medium_id(self, cr, uid, context=None):
        medium_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm', 'crm_medium_email')
        return medium_id and medium_id[1] or False

    _defaults = {
            'source_id': lambda self, *args: self._get_souce_id(*args),
            'medium_id' : lambda self, *args: self._get_medium_id(*args),
    }