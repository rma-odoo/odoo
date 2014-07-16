# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _

class ProjectTaskType(osv.Model):
    _name = 'project.task.type'
    _inherit = 'project.task.type'
    _columns = {
        'template_task_id': fields.many2one('email.template', 'Email Template For task',
                                    help="This email template will be sent to the customer of this task for rating when current stage is reached."),
    }

class Task(osv.Model):
    _name = 'project.task'
    _inherit = ['project.task','rating.model']

    def write(self, cr, uid, ids, vals, context=None):
        context = dict(context or {})
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(Task, self).write(cr, uid, ids, vals, context=context)
        if 'stage_id' in vals:
            template = self.pool['project.task.type'].browse(cr, uid, vals['stage_id'], context=context).template_task_id
            if template and template.id:
                context.update({'template_id': template.id})
                self.send_request(cr, uid, ids, context=context)
        return res

class Project(osv.Model):
    _inherit = "project.project"

    def action_rating_task(self, cr, uid, ids, context=None):
        context = dict(context or {})
        mod_obj = self.pool['ir.model.data']
        model, action_id = mod_obj.get_object_reference(cr, uid, 'rating', 'action_view_rating')
        action = self.pool['ir.actions.act_window'].read(cr, uid, action_id, context=context)
        task_ids = self.pool['project.task'].search(cr, uid, [('project_id', 'in', ids)])
        return dict(action , domain = [('res_id', 'in', task_ids), ('res_model', '=', 'project.task')])

    def _perecent_count_task(self, cr, uid, ids, field_name, arg, context=None):
        context = dict(context or {})
        tasks =  self.pool['project.task'].search(cr, uid, [('project_id', 'in', ids), ('is_rated', '=', True)], context=context)
        happy = 0
        for task_id in tasks:
            rating_happy = self.pool['rating.rating'].search(cr, uid, [('res_id', '=', task_id), ('res_model', '=', 'project.task'), ('state', '=', 'great')], context=context)
            if rating_happy:
                happy +=1
        return{id: ((happy*100) / len(tasks)) if len(tasks) else 0 for id in ids}

    _columns = {
        'percent_happy_task': fields.function(_perecent_count_task, string='% Happy', type='integer'),
    }
