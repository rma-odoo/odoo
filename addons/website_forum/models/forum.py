# -*- coding: utf-8 -*-

from datetime import datetime

import openerp
from openerp import tools
from openerp import SUPERUSER_ID
from openerp.addons.website.models.website import slug
from openerp.tools import html2plaintext
from openerp import models, fields, api, _

class KarmaError(ValueError):
    """ Karma-related error, used for forum and posts. """
    pass


class Forum(models.Model):
    """TDE TODO: set karma values for actions dynamic for a given forum"""
    _name = 'forum.forum'
    _description = 'Forums'
    _inherit = ['mail.thread', 'website.seo.metadata']

    @api.model
    def _get_default_faq(self):
        fname = openerp.modules.get_module_resource('website_forum', 'data', 'forum_default_faq.html')
        with open(fname, 'r') as f:
            return f.read()
        return False
    
    name = fields.Char(string='Name', required=True, translate=True)
    faq = fields.Html(string='Guidelines', default=_get_default_faq)
    description = fields.Html(string='Description', default='This community is for professionals and enthusiasts of our products and services.')
    # karma generation
    karma_gen_question_new = fields.Integer(string='Karma earned for new questions', default=2)
    karma_gen_question_upvote = fields.Integer(string='Karma earned for upvoting a question', default=5)
    karma_gen_question_downvote = fields.Integer(string='Karma earned for downvoting a question', default=-2)
    karma_gen_answer_upvote = fields.Integer(string='Karma earned for upvoting an answer', default=10)
    karma_gen_answer_downvote = fields.Integer(string='Karma earned for downvoting an answer', default=-2)
    karma_gen_answer_accept = fields.Integer(string='Karma earned for accepting an answer', default=2)
    karma_gen_answer_accepted = fields.Integer(string='Karma earned for having an answer accepted', default=15)
    karma_gen_answer_flagged = fields.Integer(string='Karma earned for having an answer flagged', default=-100)
    # karma-based actions
    karma_ask = fields.Integer(string='Karma to ask a new question', default=0)
    karma_answer = fields.Integer(string='Karma to answer a question', default=0)
    karma_edit_own = fields.Integer(string='Karma to edit its own posts', default=1)
    karma_edit_all = fields.Integer(string='Karma to edit all posts', default=300)
    karma_close_own = fields.Integer(string='Karma to close its own posts', default=100)
    karma_close_all = fields.Integer(string='Karma to close all posts', default=500)
    karma_unlink_own = fields.Integer(string='Karma to delete its own posts', default=500)
    karma_unlink_all = fields.Integer(string='Karma to delete all posts', default=1000)
    karma_upvote = fields.Integer(string='Karma to upvote', default=5)
    karma_downvote = fields.Integer(string='Karma to downvote', default=50)
    karma_answer_accept_own = fields.Integer(string='Karma to accept an answer on its own questions', default=20)
    karma_answer_accept_all = fields.Integer(string='Karma to accept an answers to all questions', default=500)
    karma_editor_link_files = fields.Integer(string='Karma for linking files (Editor)', default=20)
    karma_editor_clickable_link = fields.Integer(string='Karma for clickable links (Editor)', default=20)
    karma_comment_own = fields.Integer(string='Karma to comment its own posts', default=1)
    karma_comment_all = fields.Integer(string='Karma to comment all posts', default=1)
    karma_comment_convert_own = fields.Integer(string='Karma to convert its own answers to comments and vice versa', default=50)
    karma_comment_convert_all = fields.Integer(string='Karma to convert all answers to answers and vice versa', default=500)
    karma_comment_unlink_own = fields.Integer(string='Karma to unlink its own comments', default=50)
    karma_comment_unlink_all = fields.Integer(string='Karma to unlinnk all comments', default=500)
    karma_retag = fields.Integer(string='Karma to change question tags', default=75)
    karma_flag = fields.Integer(string='Karma to flag a post as offensive', default=500)

    @api.model
    def create(self, values):
        new_self = self.with_context(mail_create_nolog=True)
        return super(Forum, new_self).create(values)

class Post(models.Model):
    _name = 'forum.post'
    _description = 'Forum Post'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _order = "is_correct DESC, vote_count DESC, write_date DESC"
    
    @api.one
    def _get_user_vote(self):
        res = 0
        vote_ids = self.env['forum.post.vote'].search([('post_id', 'in', self._ids), ('user_id', '=', self._uid)])
        for vote in vote_ids:
            res = vote.vote
        self.user_vote = res

    @api.one
    @api.depends('vote_ids', 'vote_ids.vote')
    def _get_vote_count(self):
        self.vote_count = sum([int(vote.vote) for vote in self.vote_ids])

    @api.one
    def _get_user_favourite(self):
        self.user_favourite = False
        if self._uid in self.favourite_ids:
            self.user_favourite = True

    @api.one
    @api.depends('favourite_ids')
    def _get_favorite_count(self):
        self.favourite_count = len(self.favourite_ids)

    @api.one
    @api.depends('parent_id', 'child_ids')
    def _get_child_count(self):
        if self.parent_id:
            self.child_count = len(self.parent_id.child_ids)
        else:
            self.child_count = len(self.child_ids)

    @api.one
    def _get_uid_answered(self):
        self.uid_has_answered = any(answer.create_uid.id == self._uid for answer in self.child_ids)

    @api.one
    @api.depends('parent_id', 'child_ids', 'is_correct')
    def _get_has_validated_answer(self):
        self.has_validated_answer = False
        ans_ids = self.search([('parent_id', 'in', self._ids), ('is_correct', '=', True)])
        if ans_ids:
            ans_ids.has_validated_answer = True

    @api.one
    @api.depends('create_uid', 'parent_id')
    def _is_self_reply(self):
        self.self_reply = self.parent_id and self.parent_id.create_uid == self.parent_id or False

    @api.one
    def _get_post_karma_rights(self):
        user = self.env.user
        self.karma_ask = self.forum_id.karma_ask
        self.karma_answer = self.forum_id.karma_answer
        self.karma_accept = self.parent_id and self.parent_id.create_uid.id == self._uid and self.forum_id.karma_answer_accept_own or self.forum_id.karma_answer_accept_all
        self.karma_edit = self.create_uid.id == self._uid and self.forum_id.karma_edit_own or self.forum_id.karma_edit_all
        self.karma_close = self.create_uid.id == self._uid and self.forum_id.karma_close_own or self.forum_id.karma_close_all
        self.karma_unlink = self.create_uid.id == self._uid and self.forum_id.karma_unlink_own or self.forum_id.karma_unlink_all
        self.karma_upvote = self.forum_id.karma_upvote
        self.karma_downvote = self.forum_id.karma_downvote
        self.karma_comment = self.create_uid.id == self._uid and self.forum_id.karma_comment_own or self.forum_id.karma_comment_all
        self.karma_comment_convert = self.create_uid.id == self._uid and self.forum_id.karma_comment_convert_own or self.forum_id.karma_comment_convert_all
        self.can_ask = self._uid == SUPERUSER_ID or user.karma >= self.karma_ask
        self.can_answer = self._uid == SUPERUSER_ID or user.karma >= self.karma_answer
        self.can_accept = self._uid == SUPERUSER_ID or user.karma >= self.karma_accept
        self.can_edit = self._uid == SUPERUSER_ID or user.karma >= self.karma_edit
        self.can_close = self._uid == SUPERUSER_ID or user.karma >= self.karma_close
        self.can_unlink = self._uid == SUPERUSER_ID or user.karma >= self.karma_unlink
        self.can_upvote = self._uid == SUPERUSER_ID or user.karma >= self.karma_upvote
        self.can_downvote = self._uid == SUPERUSER_ID or user.karma >= self.karma_downvote
        self.can_comment = self._uid == SUPERUSER_ID or user.karma >= self.karma_comment
        self.can_comment_convert = self._uid == SUPERUSER_ID or user.karma >= self.karma_comment_convert

    name = fields.Char(string='Title')
    forum_id = fields.Many2one('forum.forum', string='Forum', required=True)
    content = fields.Html(string='Content')
    tag_ids = fields.Many2many('forum.tag', 'forum_tag_rel', 'forum_id', 'forum_tag_id', string='Tags')
    state = fields.Selection([('active', 'Active'), ('close', 'Close'), ('offensive', 'Offensive')], string='Status', default='active')
    views = fields.Integer(string='Number of Views', default=0)
    active = fields.Boolean(string='Active', default=True)
    is_correct = fields.Boolean(string='Valid Answer', help='Correct Answer or Answer on this question accepted.')
    website_message_ids = fields.One2many('mail.message', 'res_id',
        domain=lambda self: ['&', ('model', '=', self._name), ('type', 'in', ['email', 'comment'])],
        string='Post Messages', help="Comments on forum post",
    )
    # history
    create_date = fields.Datetime(string='Asked on', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string='Created by', select=True, readonly=True)
    write_date = fields.Datetime(string='Update on', select=True, readonly=True)
    write_uid = fields.Many2one('res.users', string='Updated by', select=True, readonly=True)
    # vote fields
    vote_ids = fields.One2many('forum.post.vote', 'post_id', string='Votes', default=list())
    user_vote = fields.Integer(string='My Vote', compute='_get_user_vote')
    vote_count = fields.Integer(string="Votes", compute='_get_vote_count', store=True)
    # favorite fields
    favourite_ids = fields.Many2many('res.users', string='Favourite', default=list())
    user_favourite = fields.Boolean(compute='_get_user_favourite', string="My Favourite")
    favourite_count = fields.Integer(compute='_get_favorite_count', string='Favorite Count', store=True)
    # hierarchy
    parent_id = fields.Many2one('forum.post', string='Question', ondelete='cascade')
    self_reply = fields.Boolean(string='Reply to own question', compute='_is_self_reply', store=True)
    child_ids = fields.One2many('forum.post', 'parent_id', string='Answers' , default=list())
    child_count = fields.Integer(string="Answers", compute='_get_child_count', store=True)
    uid_has_answered = fields.Boolean(string='Has Answered', compute='_get_uid_answered')
    has_validated_answer = fields.Boolean(string='Has a Validated Answered', compute='_get_has_validated_answer', store=True)
    # closing
    closed_reason_id = fields.Many2one('forum.post.reason', string='Reason')
    closed_uid = fields.Many2one('res.users', string='Closed by', select=1)
    closed_date = fields.Datetime(string='Closed on', readonly=True)
    # karma
    karma_ask = fields.Integer(string='Karma to ask', compute='_get_post_karma_rights')
    karma_answer = fields.Integer(string='Karma to answer', compute='_get_post_karma_rights')
    karma_accept = fields.Integer(string='Karma to accept this answer', compute='_get_post_karma_rights')
    karma_edit = fields.Integer(string='Karma to edit', compute='_get_post_karma_rights')
    karma_close = fields.Integer(string='Karma to close', compute='_get_post_karma_rights')
    karma_unlink = fields.Integer(string='Karma to unlink', compute='_get_post_karma_rights')
    karma_upvote = fields.Integer(string='Karma to upvote', compute='_get_post_karma_rights')
    karma_downvote = fields.Integer(string='Karma to downvote', compute='_get_post_karma_rights')
    karma_comment = fields.Integer(string='Karma to comment', compute='_get_post_karma_rights')
    karma_comment_convert = fields.Integer(string='karma to convert as a comment', compute='_get_post_karma_rights')
    # access rights
    can_ask = fields.Boolean(string='Can Ask', compute='_get_post_karma_rights')
    can_answer = fields.Boolean(string='Can Answer', compute='_get_post_karma_rights')
    can_accept = fields.Boolean(string='Can Accept', compute='_get_post_karma_rights')
    can_edit = fields.Boolean(string='Can Edit', compute='_get_post_karma_rights')
    can_close = fields.Boolean(string='Can Close', compute='_get_post_karma_rights')
    can_unlink = fields.Boolean(string='Can Unlink', compute='_get_post_karma_rights')
    can_upvote = fields.Boolean(string='Can Upvote', compute='_get_post_karma_rights')
    can_downvote = fields.Boolean(string='Can Downvote', compute='_get_post_karma_rights')
    can_comment = fields.Boolean(string='Can Comment', compute='_get_post_karma_rights', store=True)
    can_comment_convert = fields.Boolean(string='Can Convert to Comment', compute='_get_post_karma_rights')

    @api.model
    def create(self, vals):
        self = self.with_context(mail_create_nolog=True)
        post = super(Post, self).create(vals)
        # karma-based access
        if post.parent_id and not post.can_ask:
            raise KarmaError('Not enough karma to create a new question')
        elif not post.parent_id and not post.can_answer:
            raise KarmaError('Not enough karma to answer to a question')
        # messaging and chatter
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if post.parent_id:
            body = _(
                '<p>A new answer for <i>%s</i> has been posted. <a href="%s/forum/%s/question/%s">Click here to access the post.</a></p>' % 
                (post.parent_id.name, base_url, slug(post.parent_id.forum_id), slug(post.parent_id))
            )
            post.parent_id.message_post(subject=_('Re: %s') % post.parent_id.name, body=body, subtype='website_forum.mt_answer_new')
        else:
            body = _(
                '<p>A new question <i>%s</i> has been asked on %s. <a href="%s/forum/%s/question/%s">Click here to access the question.</a></p>' % 
                (post.name, post.forum_id.name, base_url, slug(post.forum_id), slug(post))
            )
            post.message_post(subject=post.name, body=body, subtype='website_forum.mt_question_new')
            self.sudo().env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_question_new)
        return post

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals['state'] in ['active', 'close'] and any(not post.can_close for post in self):
                raise KarmaError('Not enough karma to close or reopen a post.')
        if 'active' in vals:
            if any(not post.can_unlink for post in self):
                raise KarmaError('Not enough karma to delete or reactivate a post')
        if 'is_correct' in vals:
            if any(not post.can_accept for post in self):
                raise KarmaError('Not enough karma to accept or refuse an answer')
            # update karma except for self-acceptance
            mult = 1 if vals['is_correct'] else -1
            for post in self:
                if vals['is_correct'] != post.is_correct and post.create_uid.id != self._uid:
                    super_self = self.sudo()
                    super_self.env['res.users'].search([('id', '=', post.create_uid.id)]).add_karma(post.forum_id.karma_gen_answer_accepted * mult)
                    super_self.env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_answer_accept * mult)
        if any(key not in ['state', 'active', 'is_correct', 'closed_uid', 'closed_date', 'closed_reason_id'] for key in vals.keys()) and any(not post.can_edit for post in self):
            raise KarmaError('Not enough karma to edit a post.')

        res = super(Post, self).write(vals)
        # if post content modify, notify followers
        if 'content' in vals or 'name' in vals:
            for post in self:
                if post.parent_id:
                    body, subtype = _('Answer Edited'), 'website_forum.mt_answer_edit'
                    obj_id = post.parent_id
                else:
                    body, subtype = _('Question Edited'), 'website_forum.mt_question_edit'
                    obj_id = post
                obj_id.message_post(body=body, subtype=subtype)
        return res


    def close(self, reason_id):
        if any(post.parent_id for post in self):
            return False
        self.write({
            'state': 'close',
            'closed_uid': self._uid,
            'closed_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'closed_reason_id': reason_id,
        })
        return True

    @api.multi
    def unlink(self):
        if any(not post.can_unlink for post in self):
            raise KarmaError('Not enough karma to unlink a post')
        # if unlinking an answer with accepted answer: remove provided karma
        for post in self:
            if post.is_correct:
                super_self = self.sudo()
                super_self.env['res.users'].search([('id', '=', post.create_uid.id)]).add_karma(post.forum_id.karma_gen_answer_accepted * -1)
                super_self.env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_answer_accepted * -1)
        return super(Post, self).unlink()

    def vote(self, upvote=True):
        if upvote and any(not post.can_upvote for post in self):
            raise KarmaError('Not enough karma to upvote.')
        elif not upvote and any(not post.can_downvote for post in self):
            raise KarmaError('Not enough karma to downvote.')

        Vote = self.env['forum.post.vote']
        vote_ids = Vote.search([('post_id', 'in', self._ids), ('user_id', '=', self._uid)])
        new_vote = 0
        if vote_ids:
            for vote in vote_ids:
                if upvote:
                    new_vote = '0' if vote.vote == '-1' else '1'
                else:
                    new_vote = '0' if vote.vote == '1' else '-1'
                vote.vote = new_vote
        else:
            for post in self:
                new_vote = '1' if upvote else '-1'
                Vote.create({'post_id': post.id, 'vote': new_vote})
        return {'vote_count': self.vote_count, 'user_vote': new_vote}

    def convert_answer_to_comment(self, post):
        """ Tools to convert an answer (forum.post) to a comment (mail.message).
        The original post is unlinked and a new comment is posted on the question
        using the post create_uid as the comment's author. """
        if not post.parent_id:
            return False

        # karma-based action check: use the post field that computed own/all value
        if not post.can_comment_convert:
            raise KarmaError('Not enough karma to convert an answer to a comment')

        # post the message
        question = post.parent_id
        values = {
            'author_id': post.create_uid.partner_id.id,
            'body': html2plaintext(post.content),
            'type': 'comment',
            'subtype': 'mail.mt_comment',
            'date': post.create_date,
        }
        message_id = self.search([('id', '=', question.id)]).with_context(mail_create_nosubcribe=True).message_post(**values)

        # unlink the original answer, using SUPERUSER_ID to avoid karma issues
        post.sudo().unlink()

        return message_id

    def convert_comment_to_answer(self, message_id):
        """ Tool to convert a comment (mail.message) into an answer (forum.post).
        The original comment is unlinked and a new answer from the comment's author
        is created. Nothing is done if the comment's author already answered the
        question. """
        comment = self.sudo().env['mail.message'].search([('id', '=', message_id)])
        post = self.env['forum.post'].search([('id', '=', comment.res_id)])
        user = self.env.user
        if not comment.author_id or not comment.author_id.user_ids:  # only comment posted by users can be converted
            return False

        # karma-based action check: must check the message's author to know if own / all
        karma_convert = comment.author_id.id == user.partner_id.id and post.forum_id.karma_comment_convert_own or post.forum_id.karma_comment_convert_all
        can_convert = user.id == SUPERUSER_ID or user.karma >= karma_convert
        if not can_convert:
            raise KarmaError('Not enough karma to convert a comment to an answer')

        # check the message's author has not already an answer
        question = post.parent_id if post.parent_id else post
        post_create_uid = comment.author_id.user_ids[0]
        if any(answer.create_uid.id == post_create_uid.id for answer in question.child_ids):
            return False

        # create the new post
        post_values = {
            'forum_id': question.forum_id.id,
            'content': comment.body,
            'parent_id': question.id,
        }
        # done with the author user to have create_uid correctly set
        new_post_id = self.sudo(post_create_uid.id).env['forum.post'].create(post_values)

        # delete comment
        self.sudo().env['mail.message'].search([('id', '=', comment.id)]).unlink()

        return new_post_id
    
    def unlink_comment(self, post, comment):
        user = self.env.user
        if not comment.model == 'forum.post' or not comment.res_id == post.id:
            return False
        # karma-based action check: must check the message's author to know if own or all
        karma_unlink = comment.author_id.id == user.partner_id.id and post.forum_id.karma_comment_unlink_own or post.forum_id.karma_comment_unlink_all
        can_unlink = user.id == SUPERUSER_ID or user.karma >= karma_unlink
        if not can_unlink:
            raise KarmaError('Not enough karma to unlink a comment')
        return comment.sudo().unlink()
    @api.multi
    def set_viewed(self):
        self._cr.execute("""UPDATE forum_post SET views = views+1 WHERE id IN %s""", (self._ids,))
        return True

class PostReason(models.Model):
    _name = "forum.post.reason"
    _description = "Post Closing Reason"
    _order = 'name'

    name = fields.Char(string='Post Reason', required=True, translate=True)

class Vote(models.Model):
    _name = 'forum.post.vote'
    _description = 'Vote'

    post_id = fields.Many2one('forum.post', string='Post', ondelete='cascade', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self:self._uid)
    vote = fields.Selection([('1', '1'), ('-1', '-1'), ('0', '0')], string='Vote', required=True, default=lambda *args: '1')
    create_date = fields.Datetime(string='Create Date', select=True, readonly=True)
    
    def _get_karma_value(self, old_vote, new_vote, up_karma, down_karma):
        _karma_upd = {
            '-1': {'-1': 0, '0':-1 * down_karma, '1':-1 * down_karma + up_karma},
            '0': {'-1': 1 * down_karma, '0': 0, '1': up_karma},
            '1': {'-1':-1 * up_karma + down_karma, '0':-1 * up_karma, '1': 0}
        }
        return _karma_upd[old_vote][new_vote]

    @api.model
    def create(self, vals):
        vote = super(Vote, self).create(vals)
        if vote.post_id.parent_id:
            karma_value = self._get_karma_value('0', vote.vote, vote.post_id.forum_id.karma_gen_answer_upvote, vote.post_id.forum_id.karma_gen_answer_downvote)
        else:
            karma_value = self._get_karma_value('0', vote.vote, vote.post_id.forum_id.karma_gen_question_upvote, vote.post_id.forum_id.karma_gen_question_downvote)
        self.sudo().env['res.users'].search([('id', '=', vote.post_id.create_uid.id)]).add_karma(karma_value)
        return vote

    @api.multi
    def write(self, values):
        if 'vote' in values:
            for vote in self:
                if vote.post_id.parent_id:
                    karma_value = self._get_karma_value(vote.vote, values['vote'], vote.post_id.forum_id.karma_gen_answer_upvote, vote.post_id.forum_id.karma_gen_answer_downvote)
                else:
                    karma_value = self._get_karma_value(vote.vote, values['vote'], vote.post_id.forum_id.karma_gen_question_upvote, vote.post_id.forum_id.karma_gen_question_downvote)
                self.sudo().env['res.users'].search([('id', '=', vote.post_id.create_uid.id)]).add_karma(karma_value)
        res = super(Vote, self).write(values)
        return res

class Tags(models.Model):
    _name = "forum.tag"
    _description = "Tag"
    _inherit = ['website.seo.metadata']

    @api.one
    @api.depends("post_ids.tag_ids")
    def _get_posts_count(self):
        self.posts_count = len(self.post_ids)

    name = fields.Char(string='Name', required=True)
    forum_id = fields.Many2one('forum.forum', string='Forum', required=True)
    post_ids = fields.Many2many('forum.post', 'forum_tag_rel', 'forum_tag_id', 'forum_id', string='Posts')
    posts_count = fields.Integer(string="Number of Posts", compute='_get_posts_count', store=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)

