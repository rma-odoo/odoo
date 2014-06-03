import openerp
import ast, base64
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp import SUPERUSER_ID
from datetime import datetime

class website_twitter_wall(http.Controller):
    @http.route(['/twitter_walls','/twitter_wall/<model("website.twitter.wall"):wall>'], type='http', auth="public", website=True)
    def twitter_wall(self, wall=None, **kw):
        wall_obj = request.registry.get('website.twitter.wall')
        wall_ids = wall_obj.search(request.cr, SUPERUSER_ID, [], context=request.context)
        wall_list = wall_obj.browse(request.cr, SUPERUSER_ID, wall_ids, context=request.context)
        if wall:
            for walls in wall_obj.browse(request.cr, SUPERUSER_ID, [wall.id], context=request.context):
                vals = {
                        'wall_id' : wall.id, 
                        'back_image' : wall.back_image, 
                        'hashtag' : walls.tags,
                        'uid':request.session.uid or False
                }
            return request.website.render("website_twitter_wall.twitter_wall", vals)

        tweet_state = {}
        for wall in wall_list:
            pending = wall_obj._get_pending(request.cr, SUPERUSER_ID, [wall.id], '', '',context=request.context)
            published = wall_obj._get_published(request.cr, SUPERUSER_ID, [wall.id], '', '',context=request.context)
            unpublished = wall_obj._get_unpublished(request.cr, SUPERUSER_ID, [wall.id], '', '',context=request.context)
            tweet_state[wall.id] = [pending[wall.id], published[wall.id], unpublished[wall.id]]
        values = {
            'walls': wall_list,
            'status': tweet_state
        }
        return request.website.render("website_twitter_wall.twitter_walls", values)
        
    @http.route('/twitter_wall_tweet_data_admin', type='json', auth="public", website=True)
    def tweet_data_moderate(self, wall_id, published_date, state, fetch_all = True, limit = None, new_tweet_id = None, last_tweet_id = None):
        registry, cr, context = request.registry, request.cr, request.context
        tweet_obj = registry.get('website.twitter.wall.tweet')
        search_filter = [('wall_id', '=', wall_id), ('state', '=', state)]
        if new_tweet_id:
            search_filter.append(('id', '>', new_tweet_id))
        if last_tweet_id:
            search_filter.append(('id', '<', last_tweet_id))
        tweet_ids = tweet_obj.search(cr, SUPERUSER_ID, search_filter, 0, limit, order="id desc", context=context)
        tweet_objects = tweet_obj.browse(cr, SUPERUSER_ID, tweet_ids, context=context)

        tweets = []
        for tweet in tweet_objects:
            tweets.append({
                'user_image_url': tweet.user_image_url,
                'name': tweet.name,
                'description': tweet.tweet,
                'urls': [item['url'] for item in ast.literal_eval(tweet.tweet_url)],
                'media': tweet.tweet_media_ids and tweet.tweet_media_ids[0].media_url or None,
                'id': tweet.id,
                'state':tweet.state
            })
        return tweets

    @http.route('/twitter_wall_tweet_data', type='json', auth="public", website=True)
    def tweet_data(self, wall_id, published_date, state, fetch_all = False):
        search_filter = []
        if not fetch_all:
            search_filter = [('wall_id', '=', wall_id), ('published_date', '>', published_date), ('state', '=', state)]
        website_twitter_tweet = request.registry.get('website.twitter.wall.tweet')
        tweets = website_twitter_tweet.search_read(request.cr, SUPERUSER_ID, search_filter, order="id desc", context=request.context)

        data = []
        for tweet in tweets:
            #fetch date from tweet and show in this format
            created_at_date = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S")
            tweet.update({"created_at_formated_date" : created_at_date.strftime("%d %b %Y %H:%M:%S")})
            media_list = []
            for media_ids in tweet['tweet_media_ids']:
                tweet_medias = request.registry.get('website.twitter.tweet.media').search_read(request.cr, SUPERUSER_ID, [('id', '=', media_ids)], context=request.context)
                media_list += [tweet_media for tweet_media in tweet_medias]
            tweet['tweet_media_ids'] = media_list
            data.append(tweet)
        return data
    
    @http.route('/tweet_moderate/<model("website.twitter.wall"):wall>',type='http', auth='public', website=True)
    def twitter_moderate(self, wall=None, filters='pending', state=None, tweet_id=None, **kw):
        (registry, cr, context) = (request.registry, request.cr, request.context)
        if not request.session.uid: return
        state = request.registry.get('website.twitter.wall.tweet').fields_get(cr, SUPERUSER_ID, ['state'], context=None)
        values = {
            'wall': wall,
            'states': state['state']['selection']
        }
        return request.website.render('website_twitter_wall.tweet_modetate', values)

    @http.route('/tweet_moderate/state', type='json')
    def twitter_moderate_state(self, tweet_id, status):
        registry, cr, context = request.registry, request.cr, request.context
        
        tweet_obj = registry.get('website.twitter.wall.tweet')
        if status == 'published': tweet_obj.accept_tweet(cr, SUPERUSER_ID, tweet_id, context=context)
        if status == 'unpublished': tweet_obj.reject_tweet(cr, SUPERUSER_ID, tweet_id, context=context)
        return status

    @http.route('/tweet_moderate/streaming', type='json')
    def twitter_moderate_streaming(self, wall_id, state):
        registry, cr, context = request.registry, request.cr, request.context
        
        wall_obj = registry.get('website.twitter.wall')
        if state == 'startstreaming': wall_obj.start_incoming_tweets(cr, SUPERUSER_ID, [wall_id], context=context)
        if state == 'stopstreaming': wall_obj.stop_incoming_tweets(cr, SUPERUSER_ID, [wall_id], context=context)
        return state
    
    @http.route(['/twitter_wall/upload_image'], type='http', auth="public", website=True)
    def upload_image(self, type=None, id=None, upload=None, **kw):
        image_data = base64.b64encode(upload.read())
        if type == 'wall':
            image_upload_obj = request.registry.get('website.twitter.wall')
        else:
            image_upload_obj = request.registry.get('website.twitter.wall.tweet')
        image_upload_obj.write(request.cr, SUPERUSER_ID, int(id), { 'back_image': image_data }, request.context)
        return image_data