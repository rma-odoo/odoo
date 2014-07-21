# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Users(models.Model):
    _inherit = 'res.users'

    def __init__(self, pool, cr):
        init_res = super(Users, self).__init__(pool, cr) 
        self.SELF_WRITEABLE_FIELDS = list(set(
                self.SELF_WRITEABLE_FIELDS + \
                ['country_id', 'city', 'website', 'website_description', 'website_published']))
        return init_res

    @api.one
    @api.depends('badge_ids')
    def _get_user_badge_level(self):
        """Return total badge per level of users"""
        self.gold_badge, self.silver_badge, self.bronze_badge = 0, 0, 0
        for badge in self.badge_ids:
            if badge.badge_id.level == 'gold':
                self.gold_badge += 1
            elif badge.badge_id.level == 'silver':
                self.silver_badge += 1
            elif badge.badge_id.level == 'bronze':
                self.bronze_badge += 1


    create_date = fields.Datetime(string='Create Date', readonly=True, copy=False, select=True)
    karma = fields.Integer(string='Karma', default=0)
    badge_ids = fields.One2many('gamification.badge.user', 'user_id', string='Badges', copy=False)
    gold_badge = fields.Integer(string='Number of gold badges', compute="_get_user_badge_level")
    silver_badge = fields.Integer(string='Number of silver badges', compute="_get_user_badge_level")
    bronze_badge = fields.Integer(string='Number of bronze badges', compute="_get_user_badge_level")

    def add_karma(self, karma):
        self.karma += karma
        return True

    @api.model
    def get_serialised_gamification_summary(self, excluded_categories=None):
        if isinstance(excluded_categories, list):
            if 'forum' not in excluded_categories:
                excluded_categories.append('forum')
        else:
            excluded_categories = ['forum']
        return super(Users, self).get_serialised_gamification_summary()
