# -*- coding: utf-8 -*-
"""
App's models and db management.
"""

import app.const as const
from app import db, red

class User(db.Model):
    """Simple User."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
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
# When a new network is created add it to the user's list of networks.
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
    length = red.llen(_KEY_NETS_USER.format(str(user_id)))
    print " [INFO DB] net length", length
    return length if length is not None else 0

def get_user_networks(user_id):
    """Returns all the user's networks."""
    keys = red.lrange(_KEY_NETS_USER.format(str(user_id)), 0, -1)
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
    pip.rpush(_KEY_NETS_USER.format(str(user)), key)
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
    pip.lrem(_KEY_NETS_USER.format(user_id), 0, net_id)
    # Delete associated events
    events = get_user_events_network(user_id, net_id)
    for event in events:
        pip.lrem(_KEY_EVENTS_USER_DATE.format(user_id, event['date']),
                 0, event['id'])
        pip.delete(_KEY_EVENT_USER.format(event['id'], user_id))
    pip.delete(_KEY_EVENTS_USER_NET.format(user_id, net_id)) # user-network
    # Delete associated entries on wb lists
    for entry in _get_entries_network(net_id, user_id):
        # delete network from the entry, if it has one network delete entry
        if len(red.lrange(_KEY_ENTRY_LIST_NETS.format(entry['id']),
                          0, -1)) == 1:
            pip.delete(_KEY_ENTRY_USER.format(entry['id'], user_id))
            # delete from w or b list of entries
            if entry['type'] == 'B':
                pip.lrem(_KEY_ENTRY_BLACK_USER.format(user_id), 0, entry['id'])
            else:
                pip.lrem(_KEY_ENTRY_WHITE_USER.format(user_id), 0, entry['id'])
        pip.lrem(_KEY_ENTRY_LIST_NETS.format(entry['id']), 0, net_id)
    pip.execute()

# --- Events --- #
# Events are stored in hashes, which hold the event's main properties.
# The event id must be generated using _get_key_event().
# When an event is stored its ID is also added to a list of events-day
# for a given user, and to a list of events per network and user.
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
# WB lists' entries are stored in hashes, which hold the entry's main properties.
# The entry id must be generated using _get_key_entry().
# Each entry has an associated network id list,
# Each network has an associated list of wb entries
# Each user has two lists that hold the ids of  black list and white list entries.
_KEY_ENTRY_ID = 'list-entry-i-auto:'
_KEY_ENTRY_USER = 'entry:{0}:user:{1}'
_ATTR_ENTRY_TYPE = 'type'
_ATTR_ENTRY_HOST = 'host'
_ATTR_ENTRY_MAC = 'mac'
_ATTR_ENTRY_ADDR = 'addres'

_KEY_ENTRY_LIST_NETS = 'entry:{0}:list-nets'
_KEY_ENTRY_BLACK_USER = 'black:user:{0}'
_KEY_ENTRY_WHITE_USER = 'white:user:{0}'

_KEY_NET_LIST_ENTRIES = 'net:{0}:list-entries'

def _get_key_entry():
    """Returns a str with the next entry key."""
    return str(red.incr(_KEY_ENTRY_ID))

def is_entry_consistent(user_id, typ, mac, nets):
    """Check whether the new entry rule is consistent with the existing ones,
    aka not black list and white list at the same time."""
    # TODO
    return True

def _get_entries_network(net_id, user_id):
    """Gets the entries with the given network."""
    net_id = str(net_id)
    user_id = str(user_id)
    entries = red.lrange(_KEY_NET_LIST_ENTRIES.format(net_id), 0, -1)
    ret = []
    for entry in entries:
        ret.append(get_entry(user_id, entry))
    return ret

def save_entry(user_id, typ, host, mac, addr, nets):
    """Saves and entry."""
    # TODO: check mac not repeated for a network
    if typ in ['B', 'W']:
        key = _get_key_entry()
        pipe = red.pipeline()
        if typ == 'B':
            pipe.rpush(_KEY_ENTRY_BLACK_USER.format(user_id), key)
        else:
            pipe.rpush(_KEY_ENTRY_WHITE_USER.format(user_id), key)
        pipe.hset(_KEY_ENTRY_USER.format(key, user_id), _ATTR_ENTRY_TYPE, typ)
        pipe.hset(_KEY_ENTRY_USER.format(key, user_id), _ATTR_ENTRY_HOST, host)
        pipe.hset(_KEY_ENTRY_USER.format(key, user_id), _ATTR_ENTRY_MAC, mac)
        pipe.hset(_KEY_ENTRY_USER.format(key, user_id), _ATTR_ENTRY_ADDR, addr)
        for net in nets:
            pipe.rpush(_KEY_ENTRY_LIST_NETS.format(key), str(net))
            pipe.rpush(_KEY_NET_LIST_ENTRIES.format(str(net)), key)
        pipe.execute()

def get_entry(user_id, entry_id):
    """Gets an entry."""
    temp = red.hgetall(_KEY_ENTRY_USER.format(entry_id, user_id))
    if temp is not None:
        temp['id'] = entry_id
        nets = red.lrange(_KEY_ENTRY_LIST_NETS.format(entry_id), 0, -1)
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
        ents = red.lrange(_KEY_ENTRY_BLACK_USER.format(user_id), 0, -1)
    elif typ == 'W':
        ents = red.lrange(_KEY_ENTRY_WHITE_USER.format(user_id), 0, -1)
    if ents is not None:
        for ent in ents:
            tmp = get_entry(user_id, ent)
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
