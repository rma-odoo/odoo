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

{
    'name': 'Indian- Accounting Voucher',
    'version': '1.0',
    'author': 'OpenERP SA',
    'category': 'Localization/eInvoicing & Payments',
    'description': """
Voucher Report and Template
===========================

This module allows you following feature:
-----------------------------------------
    * make history for future when user change fields Amount of Payment, Partner, Write Off, Period, Journal.
    * Add new followers on voucher from all the invoice's followers attached in Account Vourcher lines
    * Add email template to be used by Finance Department to send receipt to customer once they receive Payment
    * Improve header of current voucher report such that it can display company details after title of report
""",
    'summary': 'Voucher Report, Template and invoice Followers',
    'website': 'https://www.openerp.com',
    'data': [
        'voucher_report.xml',
        'views/report_voucher.xml',
        'account_voucher_action_data.xml',
        ],
    'depends': ['account_voucher'],
    'installable': True,
}
