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
    pip.rpush(_KEY_NETS_USER.format(user), key)
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
    pip.delete(_KEY_NET.format(str(net_id)))
    pip.lrem(_KEY_NETS_USER.format(str(user_id)), 1, str(net_id))
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

_KEY_EVENTS_USER_DAY = 'event-user-day:user:{0}:day:{1}'
_KEY_EVENTS_USER_NET = 'event-user-network:user{0}:network:{1}'

def _get_key_event():
    """Returns an str with the next alert key id."""
    return str(red.incr(_KEY_EVENT_ID))

def save_event(user_id, net_id, event_desc, date, day, time, priority):
    """Saves an event."""
    key = _get_key_event()
    pipe = red.pipeline()
    pipe.lpush(_KEY_EVENTS_USER_DAY.format(user_id, date), key)
    pipe.lpush(_KEY_EVENTS_USER_NET.format(user_id, net_id), key)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DESC, event_desc)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_NET, net_id)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DATE, date)
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
    return temp

def get_user_events(user_id):
    """Returns all the events for the given user."""
    user_id = str(user_id)
    nets = get_user_networks(user_id)
    ret = []
    for net in nets:
        ret.extend(get_user_events_network(user_id, net))
    return ret

def get_user_events_day(user_id, day):
    """Returns all the events for the user for the given day."""
    user_id = str(user_id)
    events = red.lrange(_KEY_EVENTS_USER_DAY.format(user_id, day), 0, -1)
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
    evnday = red.lrange(_KEY_EVENTS_USER_DAY.format(user_id, day), 0, -1)
    interset = set(evnet) & set(evnday)
    ret = []
    for evnid in interset:
        tmp = get_event(evnid, user_id)
        if tmp is not None:
            ret.append(tmp)
    return ret
