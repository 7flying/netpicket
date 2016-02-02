# -*- coding: utf-8 -*-
"""
App's models and db management.
"""
import uuid, datetime
import app.const as const
from app import db, red

class User(db.Model):
    """Simple User."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    # If the user is logged in or not
    authenticated = db.Column(db.Boolean, default=False)

    def __init__(self, email, username):
        self.email = email
        self.username = username

    def is_active(self):
        """All users are active by default."""
        return True

    def get_id(self):
        """Return the id satisfy Flask-Login's requirements."""
        return unicode(self.id)

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False


# --- Network/buoy --- #
# Network/buoys are stored in hashes, which hold the network's main properties.
# The net id must be generated with _get_key_net()
# When a new network is created add it to the user's set of networks.
_KEY_NET_ID = 'net-id-auto:'
_KEY_NET = 'net:{0}'
_ATTR_NET_NAME = 'name'
_ATTR_NET_IFACE = 'interface'
_ATTR_NET_HADDR = 'hard-address'
_ATTR_NET_SPEED = 'speed'
_ATTR_NET_SEC = 'security'
_ATTR_NET_ADDR = 'address'
_ATTR_NET_MASK = 'subnet-mask'
_ATTR_NET_DEFR = 'default-route'
_ATTR_NET_DNS1 = 'dns-1'
_ATTR_NET_DNS2 = 'dns-2'

_KEY_NETS_USER = 'nets-user:user:{0}'

def _get_key_net():
    """Returns an str with the next network key id."""
    return str(red.incr(_KEY_NET_ID))

def get_count_user_networks(user_id):
    """Returns the number of nets. a user has."""
    length = red.scard(_KEY_NETS_USER.format(str(user_id)))
    return length if length is not None else 0

def get_user_network_ids(user_id):
    """Returns the netids for the networks of the given user."""
    return red.smembers(_KEY_NETS_USER.format(str(user_id)))

def get_user_networks(user_id):
    """Returns all the user's networks."""
    keys = red.smembers(_KEY_NETS_USER.format(str(user_id)))
    nets = []
    for key in keys:
        tmp = get_network(key)
        if tmp is not None:
            nets.append(tmp)
    return nets

def set_network(user, name, iface, haddress, speed, sec, address, submask,
                defroute, dns1, dns2=None):
    """Saves a network."""
    key = _get_key_net()
    pip = red.pipeline()
    pip.sadd(_KEY_NETS_USER.format(str(user)), key)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_NAME, name)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_IFACE, iface)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_HADDR, haddress)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_SPEED, speed)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_SEC, sec)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_ADDR, address)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_MASK, submask)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_DEFR, defroute)
    pip.hset(_KEY_NET.format(key), _ATTR_NET_DNS1, dns1)
    if dns2 != None:
        pip.hset(_KEY_NET.format(key), _ATTR_NET_DNS2, dns2)
    pip.execute()
    set_api_key(user, key, '', '', const.BUOY_NOTDEP)

def get_network(network_id):
    """Retrieves a network."""
    tmp = red.hgetall(_KEY_NET.format(str(network_id)))
    if tmp is not None:
        tmp['id'] = network_id
    return tmp

def delete_network(user_id, net_id):
    """Deletes a network."""
    pip = red.pipeline()
    user_id = str(user_id)
    net_id = str(net_id)
    pip.delete(_KEY_NET.format(net_id))
    pip.srem(_KEY_NETS_USER.format(user_id), net_id)
    # Delete associated events
    events = get_user_events_network(user_id, net_id)
    for event in events:
        pip.lrem(_KEY_EVENTS_USER_DATE.format(user_id, event['date']), 0,
                 event['id'])
        pip.delete(_KEY_EVENT_USER.format(event['id'], user_id))
    pip.delete(_KEY_EVENTS_USER_NET.format(user_id, net_id)) # user-network
    # Delete associated entries on wb lists
    for entry in get_entries_network(net_id):
        # delete network from the entry, if it has one network delete entry
        if red.scard(_KEY_ENTRY_SET_NETS.format(entry['id'])) == 1:
            pip.delete(_KEY_ENTRY.format(entry['id']))
            # delete from w or b list of entries
            if entry['type'] == 'B':
                pip.srem(_KEY_ENTRY_BLACK_USER.format(user_id), entry['id'])
            else:
                pip.srem(_KEY_ENTRY_WHITE_USER.format(user_id), entry['id'])
        pip.srem(_KEY_ENTRY_SET_NETS.format(entry['id']), 0, net_id)
    pip.execute()
    # Search for associated api keys to this network
    apik_ids = red.smembers(_KEY_APIKS_USER.format(user_id))
    for apik in apik_ids:
        tmp = red.hgetall(_KEY_APIK.format(apik))
        if tmp and tmp['network'] == net_id:
            _delete_api_key(user_id, apik)

# --- Events --- #
# Events are stored in hashes, which hold the event's main properties.
# The event id must be generated using _get_key_event().
# When an event is stored its ID is also added to a set of events-day
# for a given user, and to a set of events per network and user.
# These last have the newest event at their 0 position.
_KEY_EVENT_ID = 'event-id-auto:'
_KEY_EVENT_USER = 'event:{0}:user:{1}'
_ATTR_EVENT_DESC = 'desc'
_ATTR_EVENT_DATE = 'date' #20151126
_ATTR_EVENT_DAY = 'day' # Wed 5 Oct
_ATTR_EVENT_TIME = 'time' #6:12
_ATTR_EVENT_PRIO = 'priority'
_ATTR_EVENT_NET = 'netid'

_KEY_EVENTS_USER_DATE = 'event-user-day:user:{0}:day:{1}'
_KEY_EVENTS_USER_NET = 'event-user-network:user:{0}:network:{1}'

def _get_key_event():
    """Returns an str with the next alert key id."""
    return str(red.incr(_KEY_EVENT_ID))

def save_event(user_id, net_id, event_desc, date, day, time, priority):
    """Saves an event."""
    key = _get_key_event()
    pipe = red.pipeline()
    pipe.lpush(_KEY_EVENTS_USER_DATE.format(user_id, date), key)
    pipe.lpush(_KEY_EVENTS_USER_NET.format(user_id, net_id), key)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DESC,
              event_desc)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_NET, net_id)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DATE, date)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DAY, day)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_TIME, time)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_PRIO, priority)
    pipe.execute()

def get_event(event_id, user_id):
    """Retrieves an event."""
    temp = red.hgetall(_KEY_EVENT_USER.format(str(event_id), str(user_id)))
    if temp != None:
        temp['id'] = event_id
        net = get_network(temp[_ATTR_EVENT_NET])
        if net is not None:
            temp['net'] = (net['id'], net[_ATTR_NET_NAME])
    return temp

def get_user_events(user_id):
    """Returns all the events for the given user."""
    user_id = str(user_id)
    nets = get_user_networks(user_id)
    ret = []
    for net in nets:
        ret.extend(get_user_events_network(user_id, net))
    return ret

def get_user_events_date(user_id, date):
    """Returns all the events for the user for the given date."""
    user_id = str(user_id)
    events = red.lrange(_KEY_EVENTS_USER_DATE.format(user_id, date), 0, -1)
    ret_events = []
    for event_id in events:
        tmp = get_event(event_id, user_id)
        if tmp is not None:
            ret_events.append(tmp)
    return ret_events

def get_user_events_network(user_id, network_id):
    """Returns all the events for the given user and network."""
    user_id = str(user_id)
    network_id = str(network_id)
    events = red.lrange(_KEY_EVENTS_USER_NET.format(user_id, network_id), 0, -1)
    ret = []
    for event_id in events:
        tmp = get_event(event_id, user_id)
        if tmp is not None:
            ret.append(tmp)
    return ret

def get_user_events_day_network(user_id, network_id, day):
    """Returns the events for the given user, day and network."""
    user_id = str(user_id)
    network_id = str(network_id)
    evnet = red.lrange(_KEY_EVENTS_USER_NET.format(user_id, network_id), 0, -1)
    evnday = red.lrange(_KEY_EVENTS_USER_DATE.format(user_id, day), 0, -1)
    interset = set(evnet) & set(evnday)
    ret = []
    for evnid in interset:
        tmp = get_event(evnid, user_id)
        if tmp is not None:
            ret.append(tmp)
    return ret

# --- W/B lists' entries --- #
# WB lists' entries are stored in hashes, which hold the entry's main properties
# The entry id must be generated using _get_key_entry().
# Each entry has an associated network id set.
# Each network has an associated set of wb entries.
# Each user has two sets that hold the ids of B-list and W-list entries.
_KEY_ENTRY_ID = 'list-entry-i-auto:'
_KEY_ENTRY = 'entry:{0}'
_ATTR_ENTRY_TYPE = 'type'
_ATTR_ENTRY_HOST = 'host'
_ATTR_ENTRY_MAC = 'mac'
_ATTR_ENTRY_ADDR = 'address'

_KEY_ENTRY_SET_NETS = 'entry:{0}:set-nets'
_KEY_ENTRY_BLACK_USER = 'black:user:{0}'
_KEY_ENTRY_WHITE_USER = 'white:user:{0}'

_KEY_NET_SET_ENTRIES = 'net:{0}:set-entries'

def _get_key_entry():
    """Returns a str with the next entry key."""
    return str(red.incr(_KEY_ENTRY_ID))

def _is_entry_consistent(user_id, typ, mac, nets):
    """Check whether the new entry rule is consistent with the existing ones,
    aka not black list and white list at the same time and not repeated."""
    # Get the entries from the opposite type, check the mac
    if typ == 'B':
        sames = red.smembers(_KEY_ENTRY_BLACK_USER.format(user_id))
    else:
        sames = red.smembers(_KEY_ENTRY_WHITE_USER.format(user_id))
    if len(sames) > 0:
        for same in sames:
            entry = get_entry(same)
            if entry['mac'] == mac:
                for netid, _ in entry['nets']:
                    if netid in nets:
                        return False
    if typ == 'B':
        opposites = red.smembers(_KEY_ENTRY_WHITE_USER.format(user_id))
    else:
        opposites = red.smembers(_KEY_ENTRY_BLACK_USER.format(user_id))
    if len(opposites) > 0:
        for opp in opposites:
            entry = get_entry(opp)
            if entry['mac'] == mac:
                for netid, _ in entry['nets']:
                    if netid in nets:
                        return False
    return True

def get_entries_network(net_id):
    """Gets the entries in the given network."""
    net_id = str(net_id)
    entries = red.smembers(_KEY_NET_SET_ENTRIES.format(net_id))
    ret = [get_entry(x) for x in entries]
    return ret

def delete_entry(user_id, entry_id):
    """Deletes an entry."""
    user_id = str(user_id)
    entry_id = str(entry_id)
    auth = entry_id in red.smembers(_KEY_ENTRY_BLACK_USER.format(user_id))
    if not auth:
        auth = entry_id in red.smembers(_KEY_ENTRY_WHITE_USER.format(user_id))
    if auth:
        temp_ent = get_entry(entry_id)
        if temp_ent['type'] == 'B':
            red.srem(_KEY_ENTRY_BLACK_USER.format(user_id), entry_id)
        else:
            red.srem(_KEY_ENTRY_WHITE_USER.format(user_id), entry_id)
        red.delete(_KEY_ENTRY.format(entry_id))
        for net in red.smembers(_KEY_ENTRY_SET_NETS.format(entry_id)):
            red.srem(_KEY_NET_SET_ENTRIES.format(net), entry_id)
        red.delete(_KEY_ENTRY_SET_NETS.format(entry_id))

def save_entry(user_id, typ, host, mac, addr, nets):
    """Saves and entry."""
    user_id = str(user_id)
    consistent = _is_entry_consistent(user_id, typ, mac, nets)
    if consistent:
        if typ in ['B', 'W']:
            key = _get_key_entry()
            pipe = red.pipeline()
            if typ == 'B':
                pipe.sadd(_KEY_ENTRY_BLACK_USER.format(user_id), key)
            else:
                pipe.sadd(_KEY_ENTRY_WHITE_USER.format(user_id), key)
            pipe.hset(_KEY_ENTRY.format(key), _ATTR_ENTRY_TYPE, typ)
            pipe.hset(_KEY_ENTRY.format(key), _ATTR_ENTRY_HOST, host)
            pipe.hset(_KEY_ENTRY.format(key), _ATTR_ENTRY_MAC, mac)
            pipe.hset(_KEY_ENTRY.format(key), _ATTR_ENTRY_ADDR, addr)
            for net in nets:
                pipe.sadd(_KEY_ENTRY_SET_NETS.format(key), str(net))
                pipe.sadd(_KEY_NET_SET_ENTRIES.format(str(net)), key)
            pipe.execute()
    return consistent

def get_entry(entry_id):
    """Gets an entry."""
    entry_id = str(entry_id)
    temp = red.hgetall(_KEY_ENTRY.format(entry_id))
    if temp is not None:
        temp['id'] = entry_id
        nets = red.smembers(_KEY_ENTRY_SET_NETS.format(entry_id))
        tempnets = []
        if nets is not None:
            for net in nets:
                tempnet = get_network(net)
                tempnets.append((net, tempnet['name']))
        temp['nets'] = tempnets
    return temp

def get_entries(typ, user_id):
    """Gets all the entries of the specific type (B, W) for the given user."""
    ents = None
    ret = []
    if typ == 'B':
        ents = red.smembers(_KEY_ENTRY_BLACK_USER.format(user_id))
    elif typ == 'W':
        ents = red.smembers(_KEY_ENTRY_WHITE_USER.format(user_id))
    if ents is not None:
        for ent in ents:
            tmp = get_entry(ent)
            if tmp is not None:
                ret.append(tmp)
    return ret

# --- Hosts --- #
# Hosts are stored in hashes, which hold the host's name and a reference to
# the list of services a host has.
# We also have a set of service -> hosts (ids) with such service
# Each user has a set of hosts (ids)
# We have a set with all the known service names
_KEY_HOST_ID = 'host-id-auto:'
_KEY_HOST = 'host:{0}'
_ATTR_HOST_NAME = 'name'
_KEY_HOST_SET_SERVS = 'host-servs:host:{0}'
_KEY_SERVNAME_HOSTS = 'serv-hosts:serv:{0}'
_KEY_USER_HOSTS = 'user-hosts:user:{0}'
_KEY_SERVS = 'servs-set:'

def _get_key_host():
    """Returns a str with the next host id."""
    return str(red.incr(_KEY_HOST_ID))

def get_services():
    """Returns the set of known services."""
    return red.smembers(_KEY_SERVS)

def edit_host(user_id, host_id, hostname, servs):
    """Edits the given host."""
    user_id = str(user_id)
    host_id = str(host_id)
    if host_id in red.smembers(_KEY_USER_HOSTS.format(user_id)):
        pip = red.pipeline()
        pip.hset(_KEY_HOST.format(host_id), _ATTR_HOST_NAME, hostname)
        saved_servs = red.smembers(_KEY_HOST_SET_SERVS.format(host_id))
        # Remove all
        pip.delete(_KEY_HOST_SET_SERVS.format(host_id))
        for serv in saved_servs:
            if red.scard(_KEY_SERVNAME_HOSTS.format(serv)) == 1:
                pip.delete(_KEY_SERVNAME_HOSTS.format(serv))
                pip.srem(_KEY_SERVS, serv)
            else:
                pip.srem(_KEY_SERVNAME_HOSTS.format(serv), host_id)
        # create new associated servs
        for serv in servs:
            pip.sadd(_KEY_HOST_SET_SERVS.format(host_id), serv)
            pip.sadd(_KEY_SERVNAME_HOSTS.format(serv), host_id)
            pip.sadd(_KEY_SERVS, serv)
        pip.execute()
        return (True, 'Everything went fine!')
    else:
        return (False, 'Unknown host for the given user.')

def set_host(user_id, hostname, servs):
    """Saves a host"""
    key = _get_key_host()
    user_id = str(user_id)
    pip = red.pipeline()
    pip.sadd(_KEY_USER_HOSTS.format(user_id), key)
    pip.hset(_KEY_HOST.format(key), _ATTR_HOST_NAME, hostname)
    for serv in servs:
        pip.sadd(_KEY_HOST_SET_SERVS.format(key), serv)
        pip.sadd(_KEY_SERVNAME_HOSTS.format(serv), key)
        pip.sadd(_KEY_SERVS, serv)
    pip.execute()

def get_host(host_id):
    """Returs a host."""
    host_id = str(host_id)
    temp = red.hgetall(_KEY_HOST.format(host_id))
    if temp is not None:
        temp['id'] = host_id
        servs = red.smembers(_KEY_HOST_SET_SERVS.format(host_id))
        temp['services'] = servs
    return temp

def get_user_hosts(user_id):
    """Returns the hosts of a user"""
    hosts = red.smembers(_KEY_USER_HOSTS.format(str(user_id)))
    ret = []
    for host in hosts:
        ret.append(get_host(host))
    return ret

def delete_host(user_id, host_id):
    """Deletes a host"""
    user_id = str(user_id)
    host_id = str(host_id)
    pip = red.pipeline()
    pip.srem(_KEY_USER_HOSTS.format(user_id), host_id)
    pip.delete(_KEY_HOST.format(host_id))
    servs = red.smembers(_KEY_HOST_SET_SERVS.format(host_id))
    for serv in servs:
        if red.scard(_KEY_SERVNAME_HOSTS.format(serv)) == 1:
            pip.delete(_KEY_SERVNAME_HOSTS.format(serv))
            pip.srem(_KEY_SERVS, serv)
        else:
            pip.srem(_KEY_SERVNAME_HOSTS.format(serv), host_id)
    red.delete(_KEY_HOST_SET_SERVS.format(host_id))
    pip.execute()

# --- API keys / buoys --- #
# API keys are stored in hashes, including the key, the associated network id
# and when was created
# Each user has a set of associated keys
_KEY_APIK_ID = 'api-key-id-auto:'
_KEY_APIK = 'api-key:{0}'
_ATTR_APIK_NET = 'network'
_ATTR_APIK_KEY = 'key'
_ATTR_APIK_USER = 'userid'
_ATTR_APIK_GENERATED = 'generated'
_ATTR_APIK_STATUS = 'status'
_ATTR_APIK_LASTHOST = 'lasthost'
_ATTR_APIK_LASTSCAND = 'lastscan'
_KEY_APIKS_USER = 'api-keys:user:{0}'

_KEY_UUID_APIK = 'apik-of-uuid:{0}'

def apik_of_uuid(uuid_):
    """Given a uuid (key) retrieves the db id"""
    return red.get(_KEY_UUID_APIK.format(uuid_))

def _get_key_api():
    """Returns an str with the next api-key id."""
    return str(red.incr(_KEY_APIK_ID))

def get_user_api_keys(user_id):
    """Returns the ids of the keys the user has."""
    return red.smembers(_KEY_APIKS_USER.format(str(user_id)))

def get_api_key(apik_id):
    """Retrieves an api key."""
    apik_id = str(apik_id)
    tmp = red.hgetall(_KEY_APIK.format(apik_id))
    if tmp is not None:
        tmp['id'] = apik_id
    return tmp

def change_status(key_id, status):
    """Changes the status of a key."""
    red.hset(_KEY_APIK.format(str(key_id)), _ATTR_APIK_STATUS, status)

def set_last_host_scan(key_id, last_host, last_scan):
    """Sets the last host's ip address and scan datetime."""
    red.hset(_KEY_APIK.format(str(key_id)), _ATTR_APIK_LASTHOST, last_host)
    red.hset(_KEY_APIK.format(str(key_id)), _ATTR_APIK_LASTSCAND, last_scan)

def generate_api_key(key_id):
    """Generates an API key, set's staus to stopped."""
    key_id = str(key_id)
    new_key = uuid.uuid4()
    time = datetime.datetime.now()
    pip = red.pipeline()
    pip.set(_KEY_UUID_APIK.format(new_key), key_id)
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_KEY, new_key)
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_GENERATED,
             time.strftime(const.STRTIME_KEY_GENERATED))
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_STATUS, const.BUOY_STOPPED)
    pip.execute()
    set_action_buoy(key_id, const.BUOY_AC_STOP)

def set_api_key(userid, netid, apikey, generated_at, status):
    """Saves an api key."""
    userid = str(userid)
    netid = str(netid)
    key = _get_key_api()
    pip = red.pipeline()
    pip.sadd(_KEY_APIKS_USER.format(userid), key)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_USER, userid)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_KEY, apikey)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_NET, netid)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_GENERATED, generated_at)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_STATUS, status)
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_LASTHOST, '')
    pip.hset(_KEY_APIK.format(key), _ATTR_APIK_LASTSCAND, '')
    pip.execute()

def clean_api_key(key_id):
    """Cleans an api key."""
    key_id = str(key_id)
    tmp = red.hgetall(_KEY_APIK.format(key_id))
    red.delete(_KEY_BUOYACTION.format(key_id))
    red.delete(_KEY_UUID_APIK.format(tmp['key']))
    pip = red.pipeline()
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_KEY, '')
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_GENERATED, '')
    pip.hset(_KEY_APIK.format(key_id), _ATTR_APIK_STATUS, const.BUOY_NOTDEP)
    pip.execute()

def _delete_api_key(user_id, apik_id):
    """Deletes an api key."""
    user_id = str(user_id)
    apik_id = str(apik_id)
    # Delete uuid to key
    tmp = red.hgetall(_KEY_APIK.format(apik_id))
    red.delete(_KEY_UUID_APIK.format(tmp['key']))
    pip = red.pipeline()
    if pip.scard(_KEY_APIKS_USER.format(user_id)) == 1:
        pip.delete(_KEY_APIKS_USER.format(user_id))
    else:
        pip.srem(_KEY_APIKS_USER.format(user_id), apik_id)
    pip.delete(_KEY_APIK.format(apik_id))
    pip.execute()
    # delete also the orders a buoy must perform
    red.delete(_KEY_BUOYACTION.format(apik_id))

# --- Buoy orders --- #
_KEY_BUOYACTION = 'action:buoy:{0}'
_ATTR_BUOYACTION_TIME = 'time'
_ATTR_BUOYACTION_ACTION = 'action'

def set_action_buoy(buoy_id, action, ignore_now=False):
    """Sets the following action of a buoy"""
    buoy_id = str(buoy_id)
    red.hset(_KEY_BUOYACTION.format(buoy_id), _ATTR_BUOYACTION_ACTION, action)
    if ignore_now:
        red.hset(_KEY_BUOYACTION.format(buoy_id), _ATTR_BUOYACTION_TIME, '')
    else:
        now = datetime.datetime.now()
        red.hset(_KEY_BUOYACTION.format(buoy_id), _ATTR_BUOYACTION_TIME,
                 now.strftime(const.STRTIME_KEY_GENERATED))

def get_action_buoy(buoy_id):
    """Gets the action a buoy must complete"""
    temp = red.hgetall(_KEY_BUOYACTION.format(str(buoy_id)))
    if temp:
        temp['id'] = str(buoy_id)
    return temp

