import openerp
import ast, base64
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp import SUPERUSER_ID
from datetime import datetime
from Oauth import oauth
from openerp.addons.web.controllers.main import login_redirect, ensure_db
CACHE = {}
class website_twitter_wall(http.Controller):
    @http.route(['/twitter_walls',
                '/twitter_wall/<model("website.twitter.wall"):wall>'], type='http', auth="public", website=True)
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
                        'uid':request.session.uid or False,
                        'view_mode' : wall.view_mode
                }
            return request.website.render("website_twitter_wall.twitter_wall", vals)

        tweet_state = {}
        for wall in wall_list:
            wall_state = wall_obj._get_pending(request.cr, SUPERUSER_ID, [wall.id], '', '',context=request.context)
            tweet_state[wall.id] = [wall_state[wall.id]['pending'], wall_state[wall.id]['published'], wall_state[wall.id]['unpublished']]
        values = {
            'walls': wall_list,
            'status': tweet_state
        }
        return request.website.render("website_twitter_wall.twitter_walls", values)

class website_twitter_wall(http.Controller):
    @http.route(['/twitter_wall/<model("website.twitter.wall"):wall>/approved'], type='http', auth="public", website=True)
    def twitter_wall_approve(self, wall, **kw):
        vals = { 'wall' : wall}
        return request.website.render("website_twitter_wall.twitter_wall_approve", vals)


    @http.route('/twitter_wall_tweet_data_admin', type='json', auth="public", website=True)
    def tweet_data_moderate(self, wall_id, published_date, state, fetch_all = True, limit = None, new_tweet_id = None, last_tweet_id = None):
        return CACHE.pop(wall_id, [])

    @http.route('/twitter_wall_tweet_data', type='json', auth="public", website=True)
    def tweet_data(self, wall_id, published_date, state, fetch_all = False):
        search_filter = []
        if not fetch_all:
            search_filter = [('wall_id', '=', wall_id), ('published_date', '>', published_date), ('state', '=', state)]
        website_twitter_tweet = request.registry.get('website.twitter.wall.tweet')
        tweets = website_twitter_tweet.search_read(request.cr, SUPERUSER_ID, search_filter, context=request.context)
        for image in request.registry.get('website.twitter.wall').search_read(request.cr, SUPERUSER_ID, [('id', '=', wall_id)], ['back_image'], context=request.context):
            back_image = image['back_image']
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
            tweet['back_image'] = back_image
            data.append(tweet)
        return data

    @http.route('/twitter_wall_approved_tweet', type='json', auth="public", website=True)
    def approved_tweet_data(self, wall_id, state, limit=None, last_tweet=None):
        search_filter = [('wall_id', '=', wall_id), ('state', '=', state)]
        if last_tweet:
            search_filter.append(('id', '<', last_tweet))
        website_twitter_tweet = request.registry.get('website.twitter.wall.tweet')
        tweets = website_twitter_tweet.search_read(request.cr, SUPERUSER_ID, search_filter, [], 0, limit, order="id desc", context=request.context)

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
    def twitter_moderate_state(self, tweet, status):
        registry, cr, context = request.registry, request.cr, request.context
        wall_obj = registry.get('website.twitter.wall')
        tweet_id = wall_obj._set_tweets(cr, SUPERUSER_ID, tweet['wall_id'], tweet, context=context)

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

    @http.route('/tweet_moderate/view_mode', type='json')
    def twitter_moderate_view_mode(self, wall_id, view_mode):
        registry, cr, context = request.registry, request.cr, request.context
        wall_obj = registry.get('website.twitter.wall')
        wall_obj.write(request.cr, SUPERUSER_ID, [wall_id], { 'view_mode': view_mode }, request.context)

    @http.route(['/twitter_wall/upload_image'], type='http', auth="public", website=True)
    def upload_image(self, id=None, upload=None, **kw):
        image_data = base64.b64encode(upload.read())
        image_upload_obj = request.registry.get('website.twitter.wall')
        image_upload_obj.write(request.cr, SUPERUSER_ID, int(id), { 'back_image': image_data }, request.context)
        return image_data
    
    @http.route('/twitter_callback', type='http', auth="none")
    def twitter_callback(self, **kw):
        if not request.session.uid:
            request.params['redirect']='/twitter_callback?'+request.httprequest.query_string
            return login_redirect()
        
#         oauth_credintial = base64.standard_b64decode(request.params['oauth_credintial'])
#         oauth_credintial = dict(item.split("=") for item in oauth_credintial.split("&"))
#         print "oauth_credintial---------------->",oauth_credintial
#         website_id = int(oauth_credintial['website_id'])
        website_id = int(request.params['website_id'])
#         registry = openerp.modules.registry.RegistryManager.get(oauth_credintial['db'])
#         with registry.cursor() as cr:
        website_ids = request.registry.get("website").search(request.cr, openerp.SUPERUSER_ID, [('id','=',website_id)])
        website = request.registry.get("website").browse(request.cr, openerp.SUPERUSER_ID, website_ids, context=request.context)
        for web in website:
            access_token_response = oauth._access_token(oauth(web.twitter_api_key,web.twitter_api_secret), request.params['oauth_token'], request.params['oauth_verifier'])
            vals= {
                   'twitter_access_token' : access_token_response['oauth_token'],
                   'twitter_access_token_secret' : access_token_response['oauth_token_secret']
                   }
            request.registry.get("website").write(request.cr, openerp.SUPERUSER_ID, website_id, vals, context=request.context)

        return http.local_redirect("/twitter_walls",query=request.params)