from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import thread
import openerp.modules.registry
import logging
_logger = logging.getLogger(__name__)

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
        listner = WallListener(self.registry, self.uid, self.wall.id, self.wall.name)
        auth = OAuthHandler(self.wall.website_id.twitter_api_key, self.wall.website_id.twitter_api_secret)
        auth.set_access_token(self.wall.website_id.twitter_access_token, self.wall.website_id.twitter_access_token_secret)
        stream = Stream(auth, listner)
        tags = [tag.name for tag in self.wall.tags]
        return thread.start_new_thread(func, (tags, ))

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
            if stream_state != 'streaming': return False
            wall_obj._set_tweets(cr, openerp.SUPERUSER_ID, self.wall_id, json.loads(data), context=None)
        return True
    
    def on_status(self, status):
        return 

    def on_error(self, status):
        _logger.error('StreamListener has error for :%s ', status)
        return True

    def on_timeout(self):
        return True

    def on_disconnect(self, notice):
        return True
