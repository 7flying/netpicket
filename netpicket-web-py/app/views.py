# -*- coding: utf-8 -*-

import os

from requests_oauthlib import OAuth2Session
from flask import render_template, request, redirect, url_for, session
from flask.json import jsonify

from app import app


client_id = '25024647321-ch635ssha0lmo73lr24688slcb4mak4j.apps.googleusercontent.com'
client_secret = ''
authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
scope = ["https://www.googleapis.com/auth/userinfo.email",
         "https://www.googleapis.com/auth/userinfo.profile"]
redirect_uri = 'http://localhost:5000/callback'

@app.route('/', methods=['GET', 'POST'])
def main_page():
    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = google.authorization_url(authorization_base_url,
                                                        access_type='offline',
                                                        approval_prompt='force')

    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    google = OAuth2Session(client_id, state=session['oauth_state'])
    print request.args
    print request.__dict__
    print request.url
    print request.environ
    token = google.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.environ['QUERY_STRING'])#,
                               #code=request.args['code'])
    session['oauth_token'] = token
    r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
    print r.content
    return redirect(url_for('profile'))

@app.route('/profile', methods=['GET'])
def profile():
    return render_template('ok.html')
