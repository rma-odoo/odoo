# from tweepy.streaming import StreamListener
# from tweepy import OAuthHandler
# from tweepy import Stream
import json
import thread
import openerp.modules.registry
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
from Oauth import oauth
from streaming import StreamListener, Stream

from openerp.addons.website_twitter_wall.controllers.main import CACHE
# Temprory working this fix for linux OS, need to do more analysis after backend and frontend development.
# Remove dependency of tweepy lib in future.
class WallManager(object):
    def __init__(self, dbname, ids, wall):
        self.registry = openerp.modules.registry.RegistryManager.get(dbname)
        self.wall = wall
        self.ids = ids
    
    def start(self):
        def func(screen_names):
            return stream.filter(follow=['2446916136'])
        
        if (self.wall.state != 'not_streaming'): 
            return False
        if (self.check_api_token()):
            listner = WallListener(self.registry, self.wall.id, self.wall.name)
            auth = oauth(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
            #OAuthHandler oauth
            if(self.check_access_token()):
                auth.set_access_token(self.wall.website_id.twitter_access_token, self.wall.website_id.twitter_access_token_secret)
#                 import pdb
#                 pdb.set_trace()
#                 auth.get_user_id('openerp13')
                stream = Stream(auth, listner)
                screen_names = [screen_name.name for screen_name in self.wall.screen_name]
                thread.start_new_thread(func, (screen_names, ))
                return True
        else:
            _logger.error('Contact System Administration for Configure Twitter API KEY and ACCESS TOKEN.')
            raise osv.except_osv(_('Error Configuration!'), _('Contact System Administration for Configure Twitter API KEY and ACCESS TOKEN.')) 
            return False
    
    def check_api_token(self):
        website = self.wall.website_id
        if(website.twitter_api_key and website.twitter_api_secret):
            return True
        else:
            return False
    def check_access_token(self):
        website = self.wall.website_id
        if(website.twitter_access_token and website.twitter_access_token_secret):
            return True
        else:
            o_auth = oauth(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
            with self.registry.cursor() as cr:
                base_url = self.registry.get('ir.config_parameter').get_param(cr, openerp.SUPERUSER_ID, 'web.base.url')
                return o_auth._request_token(base_url, cr.dbname, self.wall.website_id.id)

class WallListener(StreamListener):
    def __init__(self, registry, wall_id, wall_name):
        super(WallListener, self).__init__()
        self.wall_id = wall_id
        self.registry = registry
        self.wall_name = wall_name
        self.screen_name = []
        
    def on_connect(self):
        wall_obj = self.registry.get('website.twitter.wall')
        with self.registry.cursor() as cr:
            self.screen_name = [str(screen_name['name']) for screen_name in wall_obj.browse(cr, openerp.SUPERUSER_ID, self.wall_id, context=None)['screen_name']]
        _logger.info('StreamListener Connect to Twitter API for wall: %s - %s ', self.wall_name, self.wall_id)
        return True

    def on_data(self, data):
        wall_obj = self.registry.get('website.twitter.wall')
        with self.registry.cursor() as cr:
            stream_state = wall_obj.browse(cr, openerp.SUPERUSER_ID, self.wall_id, context=None)['state']
            if stream_state != 'streaming':
                self.on_disconnect(None)
                return False
            tweet = self._process_tweet(json.loads(data))
            if tweet:wall_obj._set_tweets(cr, openerp.SUPERUSER_ID, self.wall_id, tweet, context=None)
        return True
    
    def on_status(self, status):
        _logger.info('StreamListener status for wall: %s - %s', self.wall_name, self.wall_id)
        return 

    def on_error(self, status):
        _logger.error('StreamListener has error :%s to connect with wall: %s - %s', status, self.wall_name, self.wall_id)
        raise osv.except_osv(_('Error!'), _('StreamListener has error :%s.') % (status))
        return False

    def on_timeout(self):
        _logger.warning('StreamListener timeout to connect with wall: %s - %s', self.wall_name, self.wall_id)
        return

    def on_disconnect(self, notice):
        _logger.info('StreamListener disconnect with wall: %s - %s', self.wall_name, self.wall_id)
        return False
    
    def _process_tweet(self, tweet):
        if not tweet.has_key('user'):return None
        if tweet.get('user').get('screen_name') in self.screen_name:
#             print '@',tweet.get('user').get('screen_name')
            wall_obj = self.registry.get('website.twitter.wall')
            with self.registry.cursor() as cr:
                walls = wall_obj.search_read(cr, openerp.SUPERUSER_ID, [('id', '=', self.wall_id)], ["re_tweet"])
                for wall in walls:
                    re_tweet = wall["re_tweet"]
#             print "re_twete",re_tweet
#             print "count",tweet.get('retweet_count')
#             print "/n/n",tweet.has_key('retweeted_status'),"/n/n"
            if not re_tweet:
                if tweet.has_key('retweeted_status'):return None
#                 if tweet.get('retweet_count') != 0:
            if tweet.has_key('retweeted_status'):
                tweet = tweet.get('retweeted_status')
            return tweet
#             tweets = {
#                 'name': tweet.get('user').get('name'),
#                 'screen_name': tweet.get('user').get('screen_name'),
#                 'tweet': tweet.get('text'),
#                 'tweet_url': tweet.get('entities').get('urls'),
#                 'tweet_id': tweet.get('id_str'),
#                 'created_at': tweet.get('created_at'),
#                 'user_image_url': tweet.get('user').get('profile_image_url'),
#                 'background_image_url': tweet.get('user').get('profile_background_image_url'),
#                 'wall_id': self.wall_id,
#             }
#             vals = []
#             if tweet.get('entities') and tweet.get('entities').has_key('media'):
#                 for media in tweet.get('entities').get('media'):
#                     values = {
#                         'media_id':media.get('id_str'),
#                         'media_url': media.get('media_url'),
#                         'media_url_https': media.get('media_url_https'),
#                         'url': media.get('url'),
#                         'display_url': media.get('display_url'),
#                         'expanded_url': media.get('expanded_url'),
#                         'media_height': media.get('sizes').get('small').get('h'),
#                         'media_width': media.get('sizes').get('small').get('w')
#                     }
#                     vals.append(values)
#             tweets['tweet_media_ids'] = vals
#             if self.wall_id not in CACHE:
#                 CACHE.update({self.wall_id : []})
#             CACHE[self.wall_id].append(tweets)
    #         print "\n---####----TWEET---####----",tweets,"\n"