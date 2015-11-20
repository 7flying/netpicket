# -*- coding: utf-8 -*-

import random
from flask.ext.login import login_user, logout_user, current_user,\
     login_required
from flask import render_template, redirect, url_for, g, json, Response

from app.auth import OAuthSignIn
from app import app, db, login_manager
from app.models import User


@app.route('/')
def main_page():
    """Shows main page."""
    return render_template('index.html')

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    """Requests authorization to the OAuth provider."""
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def callback(provider):
    """"Callback from the OAuth provider."""
    if not current_user.is_anonymous():
        return redirect(url_for('main_page'))
    oauth = OAuthSignIn.get_provider(provider)
    username, email = oauth.callback()
    if email is None:
        # TODO: OAuth failed -> redirect somewhere else
        return redirect(url_for('main_page'))
    # Check if the user exists in the db, else create
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email, username)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=True)
    user.authenticated = True
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard/', defaults={'section': 'timeline'})
@app.route('/dashboard/<section>')
@login_required
def dashboard(section):
    """Shows the app's dashboard. """
    return render_template('dashboard.html', section=section)

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    """ """
    return render_template('ok.html')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in the application."""
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('profile'))
    return render_template('login.html', title='Sign In')

@app.route('/logout')
@login_required
def logout():
    """Logs out the user from the application."""
    user = User.query.filter_by(id=current_user.id).first()
    logout_user()
    user.authenticated = False
    db.session.commit()
    return redirect(url_for('main_page'))

@app.before_request
def before_request():
    g.user = current_user

def event():
    while True:
        yield 'data: ' + json.dumps([x for x in range(2)]) + '\n\n'
        gevent.sleep(1)

@app.route('/stream/', methods=['GET', 'POST'])
def stream():
    return Response(event(), mimetype="text/event-stream")
