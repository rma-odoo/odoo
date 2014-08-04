# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
#
#    This program is free software: you can redistribute it and / or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv


class account_voucher(osv.Model):

    _inherit = 'account.voucher'

    _columns = {
        'amount': fields.float('Total', track_visibility='onchange', required=True,
                               readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', change_default=1,
                                      track_visibility='onchange', readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'writeoff_acc_id': fields.many2one('account.account', 'Counterpart Account',
                                           track_visibility='onchange', readonly=True,
                                           states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal',
                                      track_visibility='onchange', required=True,
                                      readonly=True, states={'draft': [('readonly', False)]}),
        'period_id': fields.many2one('account.period', 'Period', track_visibility='onchange',
                                     required=True, readonly=True,
                                     states={'draft': [('readonly', False)]}),
    }

    def get_invoice_followers(self, cr, uid, move_ids, context=None):
        message_follower_ids = []
        move_line_obj = self.pool.get('account.move.line')
        for move_id in move_ids:
            invoice = move_id and move_line_obj.browse(cr, uid, move_id, context=context).invoice
            if invoice:
                for follower in invoice.message_follower_ids:
                    if follower.id not in message_follower_ids:
                        message_follower_ids.append(follower.id)
        return message_follower_ids

    def proforma_voucher(self, cr, uid, ids, context=None):
        vals ={'message_follower_ids': []}
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type in ('sale', 'receipt'):
                move_ids = [l.move_line_id.id for l in voucher.line_cr_ids]
            elif voucher.type in ('purchase', 'payment'):
                move_ids = [l.move_line_id.id for l in voucher.line_dr_ids]
        vals['message_follower_ids'] = self.get_invoice_followers(cr, uid, move_ids, context=context)
        self.write(cr, uid, ids, vals, context=context)
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)
