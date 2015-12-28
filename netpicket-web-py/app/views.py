# -*- coding: utf-8 -*-
"""
This module holds the views of the app.
"""

import datetime, random, string, gevent, urllib
import config
import json as pyjson

from flask.ext.login import login_user, logout_user, current_user,\
     login_required
from flask import render_template, redirect, request, url_for, g, json,\
     Response, abort, flash, jsonify

from app import app, db, red, login_manager
from app.auth import OAuthSignIn
from app.forms import AddNetworkForm, AddCALEntryForm
import app.models as models
import app.const as const

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
    user = models.User.query.filter_by(email=email).first()
    if not user:
        user = models.User(email, username)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=True)
    user.authenticated = True
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard/', defaults={'section': 'timeline', 'id': ''},
           methods=['GET', 'POST', 'DELETE'])
@app.route('/dashboard/<section>/<id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def dashboard(section, id):
    """Shows the app's dashboard. """
    print "[INFO] section %s, id %s" % (section, id)
    events, lastkey, alerts, networks, acls, scans, stats = (None,) * 7
    can_acl = False # Whether the user can create or not an entry. Needs networks
    if section == const.SEC_TIMELINE:
        now = datetime.datetime.now()
        events = {}
        for i in range(const.TIMELINE_DAYS):
            date = now - datetime.timedelta(days=i)
            tempevents = models.get_user_events_date(current_user.id,
                                                     date.strftime(
                                                         const.STRTIME_DATE))
            if len(tempevents) > 0:
                events[date.strftime(const.STRTIME_DATE)] = tempevents
        lastkey = now.strftime(const.STRTIME_DATE)
    elif section == const.SEC_ALERTS:
        alerts = check_cves()
        if alerts['status'] == 400:
            alerts = None
        else:
            alerts = alerts['data']
    elif section == const.SEC_NETWORKS:
        networks = models.get_user_networks(current_user.id)
    elif section == const.SEC_ACLS:
        can_acl = models.get_count_user_networks(current_user.id) > 0
        acls = {}
        acls['W'] = models.get_entries('W', current_user.id)
        acls['B'] = models.get_entries('B', current_user.id)
        print acls
    elif section == const.SEC_SCANS:
        pass
    elif section == const.SEC_STATS:
        pass
    else:
        return abort(404)
    if request.method == 'GET':
        return render_template('dashboard.html', section=section, events=events,
                               lastkey=lastkey, cves=alerts, nets=networks,
                               acls=acls, canacl=can_acl, scans=scans,
                               stats=stats,
                               faddnet=AddNetworkForm(prefix='add-net-f'),
                               faddentry=AddCALEntryForm(
                                   prefix='add-entry-f').new(current_user.id))
    elif request.method == 'POST':
        faddnet = AddNetworkForm(request.form, prefix='add-net-f')
        faddentry = AddCALEntryForm(request.form, prefix='add-entry-f').new(
            current_user.id)
        neterrors, entryerrors, entryneterror, entryincon = (False, ) * 4
        if section == const.SEC_NETWORKS:
            if faddnet.validate_on_submit():
                nname = faddnet.name.data
                ipaddress = faddnet.ipaddress.data
                models.set_network(current_user.id, nname, '', '', '', '',
                                   ipaddress, '', '', '')
                flash('Network successfully added.', const.ALERT_SUCCESS)
                networks = models.get_user_networks(current_user.id)
            else:
                neterrors = True
        elif section == const.SEC_ACLS:
            can_acl = models.get_count_user_networks(current_user.id) > 0
            networks = [1] #faddentry.networks.data
            mac = faddentry.mac.data
            list_type = faddentry.type.data
            print networks
            print mac
            print list_type
            print " [INFO] on acls"
            if faddentry.validate_on_submit():
                print " [INFO] entry form ACK"
                if models.is_entry_consistent(current_user.id, list_type, mac,
                                              networks):
                    models.save_entry(current_user.id, list_type, '', mac,
                                      '', networks)
                else:
                    entryincon = True
            else:
                print " [INFO] entry form NACK"
                entryneterror = len(networks) == 0
                entryerrors = True
        return render_template('dashboard.html', section=section,
                               events=events, lastkey=lastkey,
                               cves=alerts, nets=networks, acls=acls,
                               canacl=can_acl, scans=scans, stats=stats,
                               faddnet=faddnet, neterrors=neterrors,
                               faddentry=faddentry, entryerrors=entryerrors,
                               entryneterror=entryneterror,
                               inconsistent=entryincon)
    elif request.method == 'DELETE':
        if section == const.SEC_NETWORKS:
            if id is not None and len(id) > 0:
                models.delete_network(current_user.id, id)
                networks = models.get_user_networks(current_user.id)
        return render_template('dashboard.html', section=section, events=events,
                               lastkey=lastkey, cves=alerts, nets=networks,
                               acls=acls, canacl=can_acl, scans=scans,
                               stats=stats,
                               faddnet=AddNetworkForm(prefix='add-net-f'),
                               faddentry=AddCALEntryForm(
                                   prefix='add-entry-f').new(current_user.id))

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    """ """
    return render_template('ok.html')

@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))

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
    user = models.User.query.filter_by(id=current_user.id).first()
    logout_user()
    user.authenticated = False
    db.session.commit()
    return redirect(url_for('main_page'))

@app.before_request
def before_request():
    g.user = current_user

def timeline_event_stream(user_id):
    """Handles timeline event notifications."""
    print " [INFO] timeline get event stream"
    pubsub = red.pubsub()
    pubsub.subscribe('timeline')
    while True:
        # {'date': 20151121, 'time': 20:24, 'day': 'Wed 14 Oct',
        # 'priority': 1, 'text': 'Hello', 'net' : 1}
        mess = pubsub.get_message()
        if config.RANDOM_TIMELINE:
            if random.randint(0, 1) == 0:
                now = datetime.datetime.now()
                text = ''.join(random.choice(string.letters) for _ in range(15))
                mess = {}
                mess['data'] = {'date': now.strftime(const.STRTIME_DATE),
                                'time': now.strftime(const.STRTIME_TIME),
                                'day': now.strftime(const.STRTIME_DAY),
                                'priority': const.PRIORITY_COLOUR[
                                    random.randint(0, 3)],
                                'text': text, 'netid': '1'}
        if mess and mess.get('data') != 1L and mess.get('data').get('text') != None:
            # Store on the db, and send it to the client
            models.save_event(user_id, mess['data']['netid'],
                              mess['data']['text'], mess['data']['date'],
                              mess['data']['day'], mess['data']['time'],
                              mess['data']['priority'])
            yield 'data: ' + json.dumps(mess.get('data')) + '\n\n'
        gevent.sleep(5)

@app.route('/timeline/', methods=['GET', 'POST'])
@login_required
def timeline():
    """Subscribe/receive timeline events."""
    print " [INFO] timeline"
    return Response(timeline_event_stream(current_user.id),
                    mimetype='text/event-stream')

@app.route('/checkstats')
@login_required
def check_stats():
    now = datetime.datetime.now()
    nets = models.get_user_networks(current_user.id)
    # order of the days
    order = []
    # net id to name
    net_idname = {}
    net_ids = []
    # per day stats
    type_count_day = {}
    net_count_day = {}
    # per week stats
    type_count_week = {'R': 0, 'O': 0, 'B': 0}
    net_count_week = {}
    for net in nets:
        net_ids.append(int(net['id']))
        net_count_week[net['id']] = 0
        net_idname[net['id']] = net['name']
    for day in range(6, -1, -1): # 6 - 0
        then = now - datetime.timedelta(days=day)
        day_str = then.strftime(const.STRTIME_DAY)
        order.append(day_str)
        type_count_day[day_str] = {'R': 0, 'O': 0, 'B': 0}
        net_count_day[day_str] = {}
        for net in nets:
            net_count_day[day_str][net['id']] = 0
        for event in models.get_user_events_date(current_user.id,
                                                 then.strftime(
                                                     const.STRTIME_DATE)):
            if event['priority'] != 'G':
                type_count_day[day_str][event['priority']] += 1
                type_count_week[event['priority']] += 1
                net_count_day[day_str][event['net'][0]] += 1
                net_count_week[event['net'][0]] += 1
    return jsonify({'status': 200, 'days' : order, 'nets' : net_idname,
                    'net_ids': net_ids, 'type_day': type_count_day,
                    'type_week': type_count_week, 'net_day': net_count_day,
                    'net_week': net_count_week})

def check_cves():
    status = 200
    response = urllib.urlopen(const.CVE_API)
    data = json.loads(response.read())
    if data is None:
        status = 400
    if status == 400:
        return {'status' : status}
    return {'status' : status, 'data' : data}
