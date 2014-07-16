# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class ProjectTaskType(osv.Model):
    _name = 'project.task.type'
    _inherit = 'project.task.type'
    _columns = {
        'template_issue_id': fields.many2one('email.template', 'Email Template For issues',
                                    help="This email template will be sent to the customer of this issue for rating when current stage is reached."),
    }

class ProjectIssue(osv.Model):
    _name = "project.issue"
    _inherit = ['project.issue','rating.model']

    def write(self, cr, uid, ids, vals, context=None):
        context = dict(context or {})
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(ProjectIssue, self).write(cr, uid, ids, vals, context=context)
        if 'stage_id' in vals:
            template = self.pool['project.task.type'].browse(cr, uid, vals['stage_id'], context=context).template_issue_id
            if template and template.id:
                context.update({'template_id': template.id})
                self.send_request(cr, uid, ids, context=context)
        return res

class Project(osv.Model):
    _inherit = "project.project"

    def action_rating_issue(self, cr, uid, ids, context=None):
        context = dict(context or {})
        mod_obj = self.pool['ir.model.data']
        model, action_id = mod_obj.get_object_reference(cr, uid, 'rating', 'action_view_rating')
        action = self.pool['ir.actions.act_window'].read(cr, uid, action_id, context=context)
        issue_ids = self.pool['project.issue'].search(cr, uid, [('project_id', 'in', ids)])
        return dict(action , domain = [('res_id', 'in', issue_ids), ('res_model', '=', 'project.issue')])

    def _perecent_count_issue(self, cr, uid, ids, field_name, arg, context=None):
        context = dict(context or {})
        issues =  self.pool['project.issue'].search(cr, uid, [('project_id', 'in', ids), ('is_rated', '=', True)], context=context)
        happy = 0
        for issue_id in issues:
            rating_happy = self.pool['rating.rating'].search(cr, uid, [('res_id', '=', issue_id), ('res_model', '=', 'project.issue'), ('state', '=', 'great')], context=context)
            if rating_happy:
                happy +=1
        return{id: ((happy*100) / len(issues)) if len(issues) else 0 for id in ids}

    _columns = {
        'percent_happy_issue': fields.function(_perecent_count_issue, string='% Happy', type='integer'),
    }
