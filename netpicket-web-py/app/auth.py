# -*- coding: utf-8 -*-
#
# Oauth with Flask, see:
# http://stackoverflow.com/questions/9499286/using-google-oauth2-with-flask
#

import json, urllib2

from flask import url_for, redirect, request
from rauth import OAuth2Service

from app import app


class OAuthSignIn(object):
    """Handles OAuth sign in with different providers."""

    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        """Requests to the service provider the authorization."""
        pass

    def callback(self):
        """Callback from the service provider."""
        pass

    def get_callback_url(self):
        """Returns our application's callback url for the given provider."""
        return url_for('callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        """Returns the provider's class."""
        if self.providers is None:
            self.providers = {}
            # Take all the subclasses and populate the providers' dict
            for provider_class in self.__subclasses__():
                self.providers[provider_class().provider_name] = provider_class()
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):

    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        googleinfo = urllib2.urlopen('https://accounts.google.com/'+\
                                     '.well-known/openid-configuration')
        google_params = json.load(googleinfo)
        self.service = OAuth2Service(name='google', client_id=self.consumer_id,
                                     client_secret=self.consumer_secret,
                                     authorize_url=google_params.get(
                                         'authorization_endpoint'),
                                     base_url=google_params.get(
                                         'userinfo_endpoint'),
                                     access_token_url=google_params.get(
                                         'token_endpoint'))

    def authorize(self):
        return redirect(self.service.get_authorize_url(scope='email',
                                                       response_type='code',
                                                       redirect_uri=
                                                       self.get_callback_url()))

    def callback(self):
        if 'code' not in request.args:
            return None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            decoder=json.loads)
        response = oauth_session.get('').json()
        return (response['name'], response['email'])
