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


from openerp.osv import osv
from openerp.osv import fields
from openerp.addons.website_twitter_wall.controllers.TwitterStream import WallManager
import datetime


class twitter_wall_settings(osv.osv_memory):

    _inherit = "website.config.settings"
    _columns = {
        'twitter_api_key': fields.related(
                        'website_id', 'twitter_api_key', type="char",
                        string='Twitter API Key',
                        help="Twitter API key you can get it from https://apps.twitter.com/app/new"),
        'twitter_api_secret': fields.related(
                        'website_id', 'twitter_api_secret', type="char",
                        string='Twitter API secret',
                        help="Twitter API secret you can get it from https://apps.twitter.com/app/new"),
        'twitter_access_token': fields.related(
                        'website_id', 'twitter_access_token', type="char",
                        string='Twitter Access Token key',
                        help="Twitter Access Token Key  you can get it from https://apps.twitter.com/app/new"),
        'twitter_access_token_secret': fields.related(
                        'website_id', 'twitter_access_token_secret', type="char",
                        string='Twitter Access Token secret',
                        help="Twitter Access Token Secret  you can get it from https://apps.twitter.com/app/new"),
    }


class TwitterClient(osv.osv):
    _inherit = "website"
    _columns = {
        'twitter_api_key': fields.char('Twitter API key', help="Twitter API Key"),
        'twitter_api_secret': fields.char('Twitter API secret', help="Twitter API Secret"),
        'twitter_access_token': fields.char('Twitter Access Token key', help="Twitter Access Token Key"),
        'twitter_access_token_secret': fields.char('Twitter Access Token secret', help="Twitter Access Token Secret"),
    }


class TwitterTweetTag(osv.osv):
    _name = "website.twitter.tweet.tag"
    _columns = {
        'name': fields.char('Twitter HashTag', size=30),
    }

class TwitterScreenName(osv.osv):
    _name = "website.twitter.screen.name"
    _columns = {
        'name': fields.char('Twitter Screen Name', size=30),
    }

class TwitterWall(osv.osv):
    _name = "website.twitter.wall"

    def _get_pending(self, cr, uid, ids, field, args, context = None):
        tweet_obj = self.pool['website.twitter.wall.tweet']
        res = {}
        for obj in tweet_obj.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'pending' : tweet_obj.search_count(cr, uid, [('wall_id','=', obj.id),('state', '=', 'pending')], context=context),
                'published' : tweet_obj.search_count(cr, uid, [('wall_id','=', obj.id),('state', '=', 'published')], context=context),
                'unpublished' : tweet_obj.search_count(cr, uid, [('wall_id','=', obj.id),('state', '=', 'unpublished')], context=context)
            }
        return res

    def _website_url(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, '')
        for wall_id in self.browse(cr, uid, ids, context=context):
            res[wall_id.id] = "/tweet_moderate/%s" % (wall_id.id,)
        return res

    _columns = {
        'name': fields.char('Wall Name'),
        'note': fields.text('Description'),
        'tags': fields.many2many('website.twitter.tweet.tag', 'rel_wall_tag', 'wall_id', 'tag_id', 'Search tags'),
        'screen_name': fields.many2many('website.twitter.screen.name', 'rel_wall_screen_name', 'wall_id', 'screen_name_id', 'Screen Name'),
        'tweet_ids': fields.one2many('website.twitter.wall.tweet', 'wall_id', 'Tweets'),
        'website_id': fields.many2one('website', 'Website'),
        'color': fields.integer('Color Index'),
        'active': fields.boolean('Avtive'),
        're_tweet': fields.boolean('Include Re-Tweet ?'),
        'state': fields.selection([('not_streaming', 'Draft'), ('streaming', 'In Progress')], string="State"),
#        'view_id': fields.many2one('ir.ui.view', 'Display Type', domain=[('model','=',)]),
        'website_published': fields.boolean('Visible in Website'),
        'back_image': fields.binary('Background Image'),
        'user_id': fields.many2one('res.users', 'Created User'),
        'pending': fields.function(_get_pending, type="integer", string='Pending Tweets', multi='status'),
        'published': fields.function(_get_pending, type="integer", string='Published Tweets', multi='status'),
        'unpublished': fields.function(_get_pending, type="integer", string='Unpublished Tweets', multi='status'),
        'view_mode' : fields.char('View Mode', size=30, required=True),
        'website_url': fields.function(_website_url, string="Website url", type="char")
    }


    _defaults = {
        'website_id': 1,# Todo: chnage 1 with first website ref
        'active': True,
        'state': 'not_streaming',
        'website_published': True,
        'view_mode' : 'list_mode',
        'user_id': lambda obj, cr, uid, ctx=None: uid,
    }

    def start_incoming_tweets(self, cr, uid, ids, context=None):
        for wall in self.browse(cr, uid, ids, context=context):
            WallManager(cr.dbname, ids, wall).start()
        self.write(cr, uid, ids, {'state': 'streaming'}, context=context)
        return True

    def stop_incoming_tweets(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'not_streaming'}, context=context)
        return True

    def _set_tweets(self, cr, uid, ids, vals, context=None):
        tweet = self.pool.get('website.twitter.wall.tweet')
        tweet_media_ids = vals['tweet_media_ids']
        del vals['tweet_media_ids']
        tweet_id = tweet.create(cr, uid, vals, context)
        if tweet_media_ids:
            tweet_media = self.pool.get('website.twitter.tweet.media')
            for tweet_data in tweet_media_ids:
                tweet_data['wall_tweet_id'] = tweet_id
                tweet_media.create(cr, uid, tweet_data, context)
        return tweet_id

    def open_wall_moderate(self, cr, uid, id, context=None):
        final_url="/tweet_moderate/"+str(id[0])
        return {'type': 'ir.actions.act_url', 'url':final_url, 'target': 'self',}

    def unlink(self, cr, uid, ids, context=None):
        twitter_obj = self.pool.get('website.twitter.wall.tweet')
        for id in ids:
            tweet_ids = twitter_obj.search(cr, uid, [('wall_id', '=', id)])
            twitter_obj.unlink(cr, uid, tweet_ids, context=context)
        return super(TwitterWall, self).unlink(cr, uid, ids, context=context)


class WebsiteTwitterTweetMedia(osv.osv):

    _name = "website.twitter.tweet.media"
    _columns = {
        'media_id': fields.char('ID',size=256),
        'media_indices_first': fields.integer('First Indice'),
        'media_indices_last': fields.integer('Last Indice'),
        'media_url': fields.char('MEDIA URL',size=256),
        'media_url_https': fields.char('URL_HTTPS',size=256),
        'url': fields.char('URL',size=256),
        'display_url': fields.char('DISPLAY URL',size=256),
        'expanded_url': fields.char('EXPANDED URL',size=256),
        'media_height': fields.integer('Height'),
        'media_width': fields.integer('Width'),
        'wall_tweet_id': fields.many2one('website.twitter.wall.tweet')
    }

#     def _process_media_tweet(self, cr, uid, tweet, tweet_id, context=None):
#         media_tweet = tweet.get('entities').get('media')
#         vals = []
#         for media in media_tweet:
#             values = {
#                 'wall_tweet_id':tweet_id,
#                 'media_id':media.get('id_str'),
#                 'media_url': media.get('media_url'),
#                 'media_url_https': media.get('media_url_https'),
#                 'url': media.get('url'),
#                 'display_url': media.get('display_url'),
#                 'expanded_url': media.get('expanded_url'),
#                 'media_height': media.get('sizes').get('small').get('h'),
#                 'media_width': media.get('sizes').get('small').get('w')
#             }
#             vals.append(values)
#         return vals


class WebsiteTwitterTweet(osv.osv):

    _name = "website.twitter.wall.tweet"
    _columns = {
        'name': fields.char('Author'),
        'screen_name':fields.char('Screen Name'),
        'tweet': fields.text('Tweet'),
        'tweet_id': fields.char('Tweet Id', size=256),
        'published_date': fields.datetime('Published on'),
        'created_at': fields.datetime('created_at'),
        'tweet_url': fields.text('Url'),
        'tweet_media_ids': fields.one2many('website.twitter.tweet.media','wall_tweet_id','Image Media'),
        'user_image_url': fields.char('Image URL', size=256),
        'background_image_url': fields.char('Background Image URL', size=256),

        'active': fields.boolean('Active'),
        'state': fields.selection([('pending', 'Pending'), ('published', 'Accept'), ('unpublished', 'Reject')], string="State"),
        'wall_id': fields.many2one('website.twitter.wall', 'Wall')
     }

    _defaults = {
        'active': True,
        'state': 'pending'
    }

    def accept_tweet(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'published','published_date': datetime.datetime.now()}, context=context)
        return

    def reject_tweet(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'unpublished','published_date':None}, context=context)
        return
        # Todo: reject tweet and remove form the wall

#     def _process_tweet(self, cr, uid, ids, tweet, context=None):
#         vals = {
#             'name': tweet.get('user').get('name'),
#             'screen_name': tweet.get('user').get('screen_name'),
#             'tweet': tweet.get('text'),
#             'tweet_url': tweet.get('entities').get('urls'),
#             'tweet_id': tweet.get('id_str'),
#             'created_at': tweet.get('created_at'),
#             'user_image_url': tweet.get('user').get('profile_image_url'),
#             'background_image_url': tweet.get('user').get('profile_background_image_url'),
#             'wall_id': ids
#         }
#         return vals