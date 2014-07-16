import openerp
import ast, base64
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp import SUPERUSER_ID
from datetime import datetime
import oauth
from openerp.addons.web.controllers.main import login_redirect, ensure_db

class website_twitter_wall(http.Controller):
    
    @http.route(['/create_twitter_wall'], type='http', auth="public", website=True)
    def create_twitter_wall(self, wall_name= None, screen_name=None, include_retweet=False, wall_description=None, **kw):
        if screen_name: screen_name_id = request.registry.get('website.twitter.screen.name').create(request.cr, SUPERUSER_ID, {'name':screen_name}, request.context)
        values = {
            'name': wall_name,
            'note': wall_description,
            're_tweet':include_retweet,
        }
        wall_id = request.registry.get('website.twitter.wall').create(request.cr, SUPERUSER_ID, values, request.context)
        if screen_name: request.cr.execute("insert into rel_wall_screen_name values('%s','%s')" % (wall_id, screen_name_id))
        return http.local_redirect("/twitter_walls",query=request.params)
    
    @http.route(['/twitter_walls',
                '/twitter_wall/<model("website.twitter.wall"):wall>'], type='http', auth="public", website=True)
    def twitter_wall(self, wall=None, **kw):
        wall_obj = request.registry.get('website.twitter.wall')
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
        
        wall_ids = wall_obj.search(request.cr, SUPERUSER_ID, [], context=request.context)
        wall_list = wall_obj.browse(request.cr, SUPERUSER_ID, wall_ids, context=request.context)
        values = {
            'walls': wall_list,
            'api_conf': True if(wall.website_id.twitter_api_key and wall.website_id.twitter_api_secret) else False,
            'api_token_conf': True if(wall.website_id.twitter_access_token and wall.website_id.twitter_access_token_secret) else False
        }
        return request.website.render("website_twitter_wall.twitter_walls", values)
    
    @http.route(['/twitter_wall/<model("website.twitter.wall"):wall>/authenticate'], type='http', auth="public", website=True)
    def authenticate_twitter_wall(self, wall, **kw):
        auth = oauth.setup(wall.website_id.twitter_api_key, wall.website_id.twitter_api_secret)
        base_url = request.registry.get('ir.config_parameter').get_param(request.cr, openerp.SUPERUSER_ID, 'web.base.url')
        auth._request_token(base_url, request.cr.dbname, 1)
        return http.local_redirect("/twitter_walls",query=request.params)
    
    @http.route(['/twitter_wall/<model("website.twitter.wall"):wall>/delete'], type='http', auth="public", website=True)
    def delete_twitter_wall(self, wall, **kw):
        request.registry.get('website.twitter.wall').unlink(request.cr, SUPERUSER_ID, [wall.id], request.context)
        return http.local_redirect("/twitter_walls",query=request.params)
    
    @http.route(['/twitter_wall/<model("website.twitter.wall"):wall>/archieve'], type='http', auth="public", website=True)
    def twitter_wall_approve(self, wall, **kw):
        vals = { 'wall' : wall}
        return request.website.render("website_twitter_wall.twitter_wall_approve", vals)

    #TODO: convert tweet_data and approved_tweet_data in to one single method
    @http.route('/twitter_wall_tweet_data', type='json', auth="public", website=True)
    def tweet_data(self, wall_id, published_date, limit=None, fetch_all = False):
        search_filter = []
        if not fetch_all:
            search_filter = [('wall_id', '=', wall_id), ('published_date', '>', published_date)]
        website_twitter_tweet = request.registry.get('website.twitter.wall.tweet')
        tweets = website_twitter_tweet.search_read(request.cr, SUPERUSER_ID, search_filter, [], 0, limit, context=request.context)
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

    #TODO: convert tweet_data and approved_tweet_data in to one single method
    @http.route('/twitter_wall_approved_tweet', type='json', auth="public", website=True)
    def approved_tweet_data(self, wall_id, limit=None, last_tweet=None):
        search_filter = [('wall_id', '=', wall_id)]
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

    @http.route('/tweet_moderate/streaming', type='json')
    def twitter_moderate_streaming(self, wall_id, state):
        registry, cr, context = request.registry, request.cr, request.context
        
        wall_obj = registry.get('website.twitter.wall')
        if state == 'startstreaming': wall_obj.start_incoming_tweets(cr, SUPERUSER_ID, [wall_id], context=context)
        if state == 'stopstreaming': wall_obj.stop_incoming_tweets(cr, SUPERUSER_ID, [wall_id], context=context)
        return state

    @http.route('/twitter_callback', type='http', auth="none")
    def twitter_callback(self, **kw):
        if not request.session.uid:
            request.params['redirect']='/twitter_callback?'+request.httprequest.query_string
            return login_redirect()
        
        website_id = int(request.params['website_id'])
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
