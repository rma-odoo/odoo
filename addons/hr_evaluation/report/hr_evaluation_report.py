# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
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

from openerp import tools
from openerp.osv import fields, osv


class hr_evaluation_report(osv.Model):
    _name = "hr.evaluation.report"
    _description = "Evaluations Statistics"
    _auto = False
    _columns = {
        'create_date': fields.date('Create Date', readonly=True),
        'delay_date': fields.float('Delay to Start', digits=(16, 2), readonly=True),
        'overpass_delay': fields.float('Overpassed Deadline', digits=(16, 2), readonly=True),
        'deadline': fields.date("Deadline", readonly=True),
        'request_id': fields.many2one('survey.user_input', 'Request_id', readonly=True),
        'closed': fields.date("closed", readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'employee_id': fields.many2one('hr.employee', "Employee", readonly=True),
        'rating': fields.selection([
            ('0', 'Significantly bellow expectations'),
            ('1', 'Did not meet expectations'),
            ('2', 'Meet expectations'),
            ('3', 'Exceeds expectations'),
            ('4', 'Significantly exceeds expectations'),
        ], "Overall Rating", readonly=True),
        'nbr': fields.integer('# of Requests', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('wait', 'Plan In Progress'),
            ('progress', 'Final Validation'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], 'Status', readonly=True),
    }
    _order = 'create_date desc'

    _depends = {
        'hr_evaluation.evaluation': [
            'create_date', 'interview_deadline', 'date_close', 'employee_id','state',
        ],
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

