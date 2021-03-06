# -*- coding: utf-8 -*-
"""
This module holds the views of the app.
"""
import datetime, random, string, gevent, ast

from flask.ext.login import login_user, logout_user, current_user,\
     login_required
from flask import render_template, redirect, request, url_for, g, json,\
     Response, abort, jsonify

from app import app, db, red, red_p, login_manager
from app.auth import OAuthSignIn
from app.forms import AddNetworkForm, AddCALEntryForm, AddHostForm
import app.models as models
import app.const as const
import app.cves as cves
import app.buoymanager as bmanager

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

def _get_sec_alerts():
    """Helper that retrieves the things needed in the alerts tab."""
    vulns = None
    alerts = cves.check_cves()
    if alerts['status'] == 400:
        alerts = None
    else:
        alerts = alerts['data']
        vulns = cves.check_vulns(alerts)
    hosts = models.get_user_hosts(current_user.id)
    return (alerts, hosts, vulns)

@app.route('/dashboard/', defaults={'section': 'timeline', 'id': ''},
           methods=['GET', 'POST', 'DELETE'])
@app.route('/dashboard/<section>/<id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def dashboard(section, id):
    """Shows the app's dashboard. """
    events, lastkey, alerts, hosts, networks, acls, scans, stats = (None,) * 8
    vulns, buoys, faddnet, faddentry, faddhost = (None,) * 5
    # Checks if the user can create acl entries or manage scans (nets required)
    can_acl, can_manage = (False,) * 2
    if section != const.SEC_TIMELINE:
        red_p.unsubscribe(const.CHAN_TIMELINE)
    if request.method == 'GET':
        if section == const.SEC_TIMELINE:
            now = datetime.datetime.now()
            events = {}
            for i in range(const.TIMELINE_DAYS):
                date = now - datetime.timedelta(days=i)
                tempevents = models.get_user_events_date(
                    current_user.id, date.strftime(const.STRTIME_DATE))
                if len(tempevents) > 0:
                    events[date.strftime(const.STRTIME_DATE)] = tempevents
                    lastkey = date.strftime(const.STRTIME_DATE)
        elif section == const.SEC_ALERTS:
            faddhost = AddHostForm(prefix='add-host-f')
            alerts, hosts, vulns = _get_sec_alerts()
        elif section == const.SEC_NETWORKS:
            faddnet = AddNetworkForm(prefix='add-net-f')
            networks = models.get_user_networks(current_user.id)
        elif section == const.SEC_ACLS:
            faddentry = AddCALEntryForm(prefix='add-entry-f').new(
                current_user.id)
            can_acl = models.get_count_user_networks(current_user.id) > 0
            acls = {'W': models.get_entries('W', current_user.id),
                    'B': models.get_entries('B', current_user.id)}
        elif section == const.SEC_SCANS:
            can_manage = models.get_count_user_networks(current_user.id) > 0
            if can_manage:
                buoys = []
                for api_id in models.get_user_api_keys(current_user.id):
                    temp = models.get_api_key(api_id)
                    if temp:
                        temp_net = models.get_network(temp['network'])
                        if temp_net:
                            buoys.append({'id': api_id,
                                          'netname': temp_net['name'],
                                          'netid': temp_net['id'],
                                          'status': temp['status'],
                                          'host': temp_net['address'],
                                          'lastscan': temp['lastscan'],
                                          'generated': temp['generated'],
                                          'key': temp['key']})
        elif section == const.SEC_STATS:
            pass
        else:
            abort(404)
        return render_template('dashboard.html', section=section, events=events,
                               lastkey=lastkey, cves=alerts, nets=networks,
                               acls=acls, canacl=can_acl, scans=scans,
                               stats=stats, hosts=hosts, vulns=vulns,
                               faddnet=faddnet, faddentry=faddentry,
                               faddhost=faddhost,
                               can_manage=can_manage, net_buoys=buoys)
    elif request.method == 'POST':
        neterrors, entryerrors, entryneterror, entryincon = (False, ) * 4
        hosterrors = False
        if section == const.SEC_NETWORKS:
            faddnet = AddNetworkForm(request.form, prefix='add-net-f')
            if faddnet.validate_on_submit():
                nname = faddnet.name.data
                ipaddress = faddnet.ipaddress.data
                models.set_network(current_user.id, nname, '', '', '', '',
                                   ipaddress, '', '', '')
            else:
                neterrors = True
            networks = models.get_user_networks(current_user.id)
        elif section == const.SEC_ALERTS:
            faddhost = AddHostForm(request.form, prefix='add-host-f')
            if faddhost.validate_on_submit():
                hname = faddhost.name.data
                hservices = faddhost.services.data
                hservices = hservices.split(',')
                hservs_clean = [x.strip() for x in hservices]
                models.set_host(current_user.id, hname.strip(), hservs_clean)
                hosts = models.get_user_hosts(current_user.id)
            else:
                hosterrors = True
            alerts, hosts, vulns = _get_sec_alerts()
        elif section == const.SEC_ACLS:
            faddentry = AddCALEntryForm(request.form, prefix='add-entry-f').new(
                current_user.id)
            can_acl = models.get_count_user_networks(current_user.id) > 0
            networks = faddentry.networks.data
            mac = (faddentry.mac.data).lower()
            list_type = faddentry.type.data
            if faddentry.validate_on_submit() and networks and len(networks) > 0:
                entryincon = models.save_entry(current_user.id, list_type,
                                              '', mac, '', networks)
                entryincon = not entryincon # the method returned consistent
            else:
                entryneterror = len(networks) == 0
                entryerrors = True
            acls = {'W': models.get_entries('W', current_user.id),
                    'B': models.get_entries('B', current_user.id)}
        return render_template('dashboard.html', section=section,
                               events=events, lastkey=lastkey,
                               cves=alerts, nets=networks, acls=acls,
                               canacl=can_acl, scans=scans, stats=stats,
                               hosts=hosts, vulns=vulns,
                               faddhost=faddhost, hosterrors=hosterrors,
                               faddnet=faddnet, neterrors=neterrors,
                               faddentry=faddentry, entryerrors=entryerrors,
                               entryneterror=entryneterror,
                               inconsistent=entryincon)
    elif request.method == 'DELETE':
        if section == const.SEC_NETWORKS:
            if id is not None and len(id) > 0:
                models.delete_network(current_user.id, id)
                networks = models.get_user_networks(current_user.id)
        elif section == const.SEC_ALERTS:
            if id is not None and len(id) > 0:
                models.delete_host(current_user.id, id)
                hosts = models.get_user_hosts(current_user.id)
        elif section == const.SEC_ACLS:
            if id is not None and len(id) > 0:
                models.delete_entry(current_user.id, id)
                acls = {'W': models.get_entries('W', current_user.id),
                        'B': models.get_entries('B', current_user.id)}
        return render_template('dashboard.html', section=section, events=events,
                               lastkey=lastkey, cves=alerts, nets=networks,
                               acls=acls, canacl=can_acl, scans=scans,
                               stats=stats, hosts=hosts, vulns=vulns,
                               faddhost=AddHostForm(prefix='add-host-f'),
                               faddnet=AddNetworkForm(prefix='add-net-f'),
                               faddentry=AddCALEntryForm(
                                   prefix='add-entry-f').new(current_user.id))

@app.route('/host/<int:hid>', methods=['POST'])
@login_required
def manage_host(hid):
    """Edits a host."""
    temp_servs = request.form.get('edit-host-f-services')
    temp_name = request.form.get('edit-host-f-name')
    hostediterrors = None
    if temp_servs is None or (len(temp_servs) < 1 or len(temp_servs) > 300):
        hostediterrors = {}
        hostediterrors['services'] = True
    if temp_name is None or (len(temp_name) < 1 or len(temp_name) > 30):
        if hostediterrors is None:
            hostediterrors = {}
        hostediterrors['name'] = True
    if hostediterrors is None:
        servs = [x.strip() for x in
                 request.form.get('edit-host-f-services').split(',')]
        ret = models.edit_host(current_user.id, hid,
                               request.form.get('edit-host-f-name'), servs)
        if not ret[0]:
            hostediterrors = dict(services=True, name=True)
    if hostediterrors is None:
        return redirect(url_for('dashboard', section=const.SEC_ALERTS,
                                id='default'))
    else:
        alerts, hosts, vulns = _get_sec_alerts()
        return render_template('dashboard.html', section=const.SEC_ALERTS,
                               cves=alerts, hosts=hosts, vulns=vulns,
                               hostediterrors=hostediterrors, hosterror=hid,
                               faddhost=AddHostForm(prefix='add-host-f'))

@app.route('/apikey/<int:key_id>', methods=['POST', 'DELETE'])
@login_required
def manage_key(key_id):
    """Generates and deletes api keys."""
    if request.method == 'POST':
        if str(key_id) in models.get_user_network_ids(current_user.id):
            models.generate_api_key(key_id)
            return jsonify({'status': 200})
        else:
            return jsonify({'status': 404,
                            'message': 'User has no such network.'})
    elif request.method == 'DELETE':
        if str(key_id) in models.get_user_api_keys(current_user.id):
            models.clean_api_key(key_id)
            return jsonify({'status': 200})
        else:
            return jsonify({'status': 404,
                            'message': 'User has no such key.'})

@app.route('/buoy/<int:buo_id>/<action>', methods=['PUT'])
@login_required
def manage_buoy(buo_id, action):
    """Starts or stops the given buoy."""
    if action in [const.BUOY_AC_LAUNCH, const.BUOY_AC_STOP] and \
        str(buo_id) in models.get_user_api_keys(current_user.id):
        bmanager.set_action(buo_id, action, now=True)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 404, 'message': 'Wrong params.'})

@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))

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
    red_p.subscribe(const.CHAN_TIMELINE)
    while True:
        # {'date': 20151121, 'time': 20:24, 'day': 'Wed 14 Oct',
        # 'priority': 1, 'text': 'Hello', 'net' : 1, 'netname': 'Home 2'}
        mess = red_p.get_message()
        if app.config['RANDOM_TIMELINE']:
            if random.randint(0, 1) == 0:
                now = datetime.datetime.now()
                text = ''.join(random.choice(string.letters) for _ in range(15))
                mess = {}
                netid = str(random.choice(list(
                    models.get_user_network_ids(user_id))))
                net = models.get_network(netid)
                mess['data'] = {'date': now.strftime(const.STRTIME_DATE),
                                'time': now.strftime(const.STRTIME_TIME),
                                'day': now.strftime(const.STRTIME_DAY),
                                'priority': const.PRIORITY_COLOUR[
                                    random.randint(0, 3)],
                                'text': text, 'netid': netid,
                                'netname': net['name']}
        if mess:
            mess = ast.literal_eval(mess['data'])
            # Send it to the client
            yield 'data: ' + json.dumps(mess) + '\n\n'
        gevent.sleep(1)

@app.route('/timeline/', methods=['GET', 'POST'])
@login_required
def timeline():
    """Subscribe/receive timeline events."""
    return Response(timeline_event_stream(current_user.id),
                    mimetype='text/event-stream')

@app.route('/checkstats')
@login_required
def check_stats():
    """Returns a json with the latests statistics."""
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

