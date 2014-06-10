from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import thread
import openerp.modules.registry
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
from Oauth import oauth

# Temprory working this fix for linux OS, need to do more analysis after backend and frontend development.
# Remove dependency of tweepy lib in future.
class WallManager(object):
    def __init__(self, dbname, uid, wall):
        self.registry = openerp.modules.registry.RegistryManager.get(dbname)
        self.uid = uid
        self.wall = wall

    def start(self):
        def func(tags):
            return stream.filter(track=tags)
        
        if (self.wall.state != 'not_streaming'): 
            return False
        if (self.check_api_token()):
            listner = WallListener(self.registry, self.uid, self.wall.id, self.wall.name)
            auth = OAuthHandler(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
            
            auth.set_access_token(self.wall.website_id.twitter_access_token, self.wall.website_id.twitter_access_token_secret)
            stream = Stream(auth, listner)
            tags = [tag.name for tag in self.wall.tags]
            thread.start_new_thread(func, (tags, ))
            return True
            
            
#             listner = WallListener(self.registry, self.uid, self.wall.id, self.wall.name)
#             auth = OAuthHandler(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
#             
#             auth.set_access_token(self.wall.website_id.twitter_access_token, self.wall.website_id.twitter_access_token_secret)
#             stream = Stream(auth, listner)
#             tags = [tag.name for tag in self.wall.tags]
#             thread.start_new_thread(func, (tags, ))
#             return True
        else:
            _logger.error('Contact System Administration for Configure Twitter API KEY and ACCESS TOKEN.')
            raise osv.except_osv(_('Error Configuration!'), _('Contact System Administration for Configure Twitter API KEY and ACCESS TOKEN.')) 
            return False
    
    def check_api_token(self):
        website = self.wall.website_id
        if(website.twitter_api_key and website.twitter_api_secret):
            if(website.twitter_access_token and website.twitter_access_token_secret):
                return True
            else:
                o_auth = oauth(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
                with self.registry.cursor() as cr:
                    base_url = self.registry.get('ir.config_parameter').get_param(cr, openerp.SUPERUSER_ID, 'web.base.url')
                    return o_auth._request_token(base_url, cr.dbname, self.wall.website_id.id)
        else:
            return False

class WallListener(StreamListener) :
    def __init__(self, registry, uid, wall_id, wall_name):
        super(WallListener, self).__init__()
        self.uid = uid
        self.wall_id = wall_id
        self.registry = registry
        self.wall_name = wall_name
        
    def on_connect(self):
        _logger.info('StreamListener Connect to Twitter API for wall: %s - %s ', self.wall_name, self.wall_id)
        return True

    def on_data(self, data):
        wall_obj = self.registry.get('website.twitter.wall')
        with self.registry.cursor() as cr:
            stream_state = wall_obj.browse(cr, openerp.SUPERUSER_ID, self.wall_id, context=None)['state']
            if stream_state != 'streaming':
                self.on_disconnect(None)
                return False
            wall_obj._set_tweets(cr, openerp.SUPERUSER_ID, self.wall_id, json.loads(data), context=None)
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
