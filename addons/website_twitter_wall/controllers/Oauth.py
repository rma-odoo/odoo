from urllib2 import urlopen, Request, HTTPError, quote
from hashlib import sha1
import base64
import json
import random
import hmac
import time
import lxml.html

class oauth(object):
    
    def __init__(self, API_key, API_secret):
        # Server Links
        self.REQUEST_URL = "https://api.twitter.com/oauth/request_token";
        self.AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize";
        self.ACCESS_URL = "https://api.twitter.com/oauth/access_token";
        
        # Consumer keys
        self.API_key = API_key  # "Xcf3Sq3PiONQjX0pg560vI28m"
        self.API_secret = API_secret  # "s3gbksdBkI8Ou9FOkYhurwgejyrPEGHJfosPuqJjsgrtv1yFOO"
        self.Oauth_Token = None
        self.Oauth_Token_Secret = None
        
    def _get_nonce(self):
        NONCE = ""
        for i in range(32):
            NONCE += chr(random.randint(97, 122))
        return NONCE
    
    def _get_timestamp(self):
        return str(int(time.time()))
    
    def _generate_header(self, URL, signature_method, oauth_version, callback_url = None, request_token=None, oauth_verifier = None, params=None):
        HEADER = ''
        if callback_url: HEADER += 'oauth_callback="' + quote(callback_url, '') + '", '
        if request_token: HEADER += 'oauth_token="' + request_token + '", '
        if oauth_verifier: HEADER += 'oauth_verifier="' + oauth_verifier + '", '
        HEADER += 'oauth_consumer_key="' + self.API_key + '", '
        HEADER += 'oauth_nonce="' + self._get_nonce() + '", '
        HEADER += 'oauth_signature_method="' + signature_method + '", '
        HEADER += 'oauth_timestamp="' + self._get_timestamp() + '", '
        if self.Oauth_Token: HEADER += 'oauth_token="' + self.Oauth_Token + '", '
        HEADER += 'oauth_version="' + oauth_version + '"'
        HEADER += ', oauth_signature="' + self._build_signature(URL, HEADER, params) + '"'
        return 'OAuth realm="", ' + HEADER
    
    def _build_signature(self, URL, HEADER, params):
        PARAMETER_STRING = ''
        if params:
            PARAMETER_STRING = "delimited=length&" + self._header_to_parameter(HEADER)+"&track=test"
        else:
            PARAMETER_STRING = self._header_to_parameter(HEADER)
        print "PARAMETER_STRING",PARAMETER_STRING
        BASE_STRING = 'POST&' + quote(URL, '') + '&' + quote(PARAMETER_STRING, '')
        SIGNING_KEY = quote(self.API_secret, '') + '&' + (quote(self.Oauth_Token_Secret, '') if self.Oauth_Token_Secret else '')
        print("DEBUG : SIGNING KEY " + SIGNING_KEY + " BASE STRING " + BASE_STRING + "\n")
        return quote(base64.standard_b64encode(hmac.new(SIGNING_KEY.encode(), BASE_STRING.encode(), sha1).digest()).decode('ascii'))
    
    def _header_to_parameter(self, HEADER):
        PARAMETER_STRING = HEADER.replace(", ", "&")
        PARAMETER_STRING = PARAMETER_STRING.replace("\"", "")
        return PARAMETER_STRING
    
    def _string_to_dict(self, request_response):
        return dict(item.split("=") for item in request_response.split("&"))
    
    def _request_token(self, base_url, dbname, website_id):
        # oauth_credintial = base64.standard_b64encode("db=" + dbname + "&website_id=" + str(website_id) + "&oauth_token ="+self.API_key + "&oauth_secret ="+ self.API_secret)
        # callback_url = base_url + "/web/login?db=" + dbname + "&redirect=/twitter_callback#oauth_credintial=" + oauth_credintial   # "http://127.0.0.1:8069/"
        callback_url = base_url + "/twitter_callback?db=" + dbname + "&website_id=" + str(website_id)  # "http://127.0.0.1:8069/"
        HEADER = self._generate_header(self.REQUEST_URL, 'HMAC-SHA1', '1.0', callback_url = callback_url)

        HTTP_REQUEST = Request(self.REQUEST_URL)
        HTTP_REQUEST.add_header('Authorization', HEADER)
        request_response = urlopen(HTTP_REQUEST, '').read()
        request_response = self._string_to_dict(request_response)

        #Call authorize token method
        if request_response['oauth_token'] and request_response['oauth_callback_confirmed']:
            return self._authorize_token(request_response['oauth_token'])
        return False
    
    def _authorize_token(self, request_token):
        url = self.AUTHORIZE_URL + "?oauth_token=" + request_token
        import webbrowser
        import sys
        if sys.platform == 'win32':
            res = webbrowser.open(url.decode('utf-8'))
        else:
            res = webbrowser.open(url, new=0, autoraise=True)
        return True
    
    def _access_token(self, request_token, oauth_verifier):
        HEADER = self._generate_header(self.ACCESS_URL, 'HMAC-SHA1', '1.0', request_token = request_token, oauth_verifier = oauth_verifier)
            
        HTTP_REQUEST = Request(self.ACCESS_URL)
        HTTP_REQUEST.add_header('Authorization', HEADER)
        access_token_response = urlopen(HTTP_REQUEST, '').read()
        access_token_response = self._string_to_dict(access_token_response)
        return access_token_response
    
    def set_access_token(self, Oauth_Token, Oauth_Token_Secret):
        self.Oauth_Token = Oauth_Token
        self.Oauth_Token_Secret = Oauth_Token_Secret        