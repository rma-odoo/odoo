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

import time
from openerp import models,api 
from openerp.tools import amount_to_text_en

class ReportVoucher(models.AbstractModel):
    _name = 'report.l10n_in_account_voucher.report_voucher'

    @api.model
    def render_html(self, ids, data=None):
        report_obj = self.env['report']
        voucher_obj = self.env['account.voucher']
        report = report_obj._get_report_from_name('l10n_in_account_voucher.report_voucher')
        selected_orders = voucher_obj.search([('id', 'in', ids)])

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': selected_orders,
            'time': time,
            'convert':self.convert,
            'get_title': self.get_title,
            'debit':self.debit,
            'credit':self.credit,
            'get_ref':self._get_ref
        }
        return report_obj.render('l10n_in_account_voucher.report_voucher', docargs)

    def convert(self, amount, cur):
        return amount_to_text_en.amount_to_text(amount, 'en', cur)

    def get_title(self, type):
        title = ''
        if type:
            title = type[0].swapcase() + type[1:] + " Voucher"
        return title

    def debit(self, move_ids):
        debit = 0.0
        for move in move_ids:
            debit += move.debit
        return debit

    def credit(self, move_ids):
        credit = 0.0
        for move in move_ids:
            credit += move.credit
        return credit

    @api.model
    def _get_ref(self, voucher_id, move_ids):
        voucher = self.env['account.voucher.line'].search([('partner_id', '=', move_ids.partner_id.id), ('voucher_id', '=', voucher_id)])
        if voucher:
            return voucher[0].name
        else:
            return
