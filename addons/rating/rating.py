# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class Rating(osv.Model):
    _name = "rating.rating"
    _columns = {
        'res_model': fields.char('Resource Model', required=True),
        'res_id': fields.integer('Resource ID', required=True),
        'user_id' : fields.many2one('res.users', 'Rated User'),
        'customer_id' : fields.many2one('res.partner', 'Customer'),
        'state': fields.selection([('great', 'Great'),('okay', 'Okay'),('bad', 'Not Good')], 'Select Rate', required=True),
    }

class RatingModel(osv.AbstractModel):
    _name = 'rating.model'

    _columns = {
        'is_rated': fields.boolean('Is Rated'),
    }

    def send_request(self, cr, uid, ids, context=None):
        """
            Sends an email to the customer requesting rating
            for the Model's object from which it is called.
        """
        context = dict(context or {})
        mail_ids = []
        for id in ids:
            values  = self.pool['email.template'].generate_email(cr, uid, context['template_id'], self.browse(cr, uid, id,context).id, context=context)
            if values.get('email_from') and values.get('email_to'):
                mail_ids.append(self.pool['email.template'].send_mail(cr, uid, context['template_id'], self.browse(cr, uid, id,context).id, force_send=True, context=context))
        return mail_ids if mail_ids else False