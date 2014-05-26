import openerp
import ast
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
# from openerp import tools
# import time
from datetime import datetime

class website_twitter_wall(http.Controller):
    @http.route('/twitter_walls', type='http', auth="public", website=True)
    def twitter_wall(self, **kw):
        wall_obj = request.registry.get('website.twitter.wall')
        wall_ids = wall_obj.search(request.cr, openerp.SUPERUSER_ID, [], context=request.context)
        wall = wall_obj.browse(request.cr, openerp.SUPERUSER_ID, wall_ids, context=request.context)
        values = { 'walls': wall }
        return request.website.render("website_twitter_wall.twitter_walls", values)
    
    @http.route('/twitter_wall_tweet/<model("website.twitter.wall"):wall>', type='http', auth="public", website=True)
    def twitter_wall_tweet(self, wall=None, **kw):
        
        for walls in request.registry.get('website.twitter.wall').browse(request.cr, request.uid, 
                                                                            [wall.id],  
                                                                            context=request.context):
            vals = {'wall_id' : wall.id, 'hashtag' : walls.tags}
        return request.website.render("website_twitter_wall.twitter_wall_tweet", vals)
    
    @http.route('/twitter_wall_tweet_data_admin', type='json', auth="public", website=True)
    def tweet_data_moderate(self, wall_id, published_date, state, fetch_all = True):
        registry, cr, uid, context = request.registry, request.cr, request.uid, request.context
        tweet_obj = registry.get('website.twitter.wall.tweet')
        tweet_ids = tweet_obj.search(cr, uid, [('wall_id', '=', wall_id), ('state', '=', state)], context=context)
        tweet_objects = tweet_obj.browse(cr, uid, tweet_ids, context=context)

        tweets = []
        for tweet in tweet_objects:
            tweets.append({
                'user_image_url': tweet.user_image_url,
                'name': tweet.name,
                'description': tweet.tweet,
                'urls': [item['url'] for item in ast.literal_eval(tweet.tweet_url)],
                'media': tweet.tweet_media_ids and tweet.tweet_media_ids[0].media_url or None,
                'id': tweet.id
            })
        return tweets

    @http.route('/twitter_wall_tweet_data', type='json', auth="public", website=True)
    def tweet_data(self, wall_id, published_date, state, fetch_all = False):
        search_filter = []
        if not fetch_all:
            search_filter = [('wall_id', '=', wall_id), ('published_date', '>', published_date), ('state', '=', state)]
        website_twitter_tweet = request.registry.get('website.twitter.wall.tweet')
        tweets = website_twitter_tweet.search_read(request.cr, openerp.SUPERUSER_ID, search_filter, context=request.context)

        data = []
        for tweet in tweets:
            #fetch date from tweet and show in this format
            created_at_date = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S")
            tweet.update({"created_at_formated_date" : created_at_date.strftime("%d %b %Y %H:%M:%S")})
            media_list = []
            for media_ids in tweet['tweet_media_ids']:
                tweet_medias = request.registry.get('website.twitter.tweet.media').search_read(request.cr, openerp.SUPERUSER_ID, [('id', '=', media_ids)], context=request.context)
                media_list += [tweet_media for tweet_media in tweet_medias]
            tweet['tweet_media_ids'] = media_list
            data.append(tweet)
        return data
    
    @http.route('/tweet_moderate/<model("website.twitter.wall"):wall>',type='http', auth='public', website=True)
    def twitter_moderate(self, wall=None, filters='pending', state=None, tweet_id=None, **kw):
        (registry, cr, uid, context) = (request.registry, request.cr, request.uid, request.context)
        state = request.registry.get('website.twitter.wall.tweet').fields_get(cr, uid, ['state'], context=None)
        values = {
            'wall': wall,
            'states': state['state']['selection']
        }
        return request.website.render('website_twitter_wall.tweet_modetate', values)

    @http.route('/twitter_wall/upload_image',type='http', auth='public', website=True)
    def twitter_wall_upload_image(self, func, upload=None, **kw):
        image_data = upload.read()
        request.registry.get('website.twitter.wall.tweet').write(request.cr, request.uid, 7254, {
            'back_image': image_data.encode('base64'),
            }, request.context)
        return """<script type='text/javascript'>
            window.location.href = '%s';
        </script>""" % (func)