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

# ---- Keys ---- #
USER = 'user:'

F_NETWORK = 'network'

# --- User-Networks --- #

def set_network(user, nname):
    # something
    _l_set_network(user, nname)

def delete_network(user, nname):
    # something
    _l_del_network(user, nname)

# -- List of all Networks a user has -- #

def _l_set_network(user, nname):
    pass

def _l_del_network(user, nname):
    pass

# --- Events --- #
# Events are stored in hashes, which hold the event's main properties.
# The event id must be generated using _get_key_event().
# When an event is stored its ID is also added to a list of events-day
# for a given user. This last has the newest event at its 0 position.
_KEY_EVENT_ID = 'event-id-auto:'
_KEY_EVENT_USER = 'event:{0}:user:{1}'
_ATTR_EVENT_DESC = 'desc'
_ATTR_EVENT_DATE = 'date' #20151126
_ATTR_EVENT_DAY = 'day' # Wed 5 Oct
_ATTR_EVENT_TIME = 'time' #6:12
_ATTR_EVENT_PRIO = 'priority'

_KEY_EVENTS_USER_DAY = 'event-ids:user:{0}:day:{1}'

def _get_key_event():
    """Returns an str with the next alert key id."""
    ret = red.incr(_KEY_EVENT_ID)
    return str(ret)

def save_event(user_id, event_desc, date, day, time, priority):
    """Saves an alert."""
    key = _get_key_event()
    print "save event key:", _KEY_EVENT_USER.format(key, user_id)
    pipe = red.pipeline()
    pipe.lpush(_KEY_EVENTS_USER_DAY.format(user_id, date), key)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DESC, event_desc)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DATE, date)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_DAY, day)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_TIME, time)
    pipe.hset(_KEY_EVENT_USER.format(key, user_id), _ATTR_EVENT_PRIO, priority)
    pipe.execute()

def get_event(event_id, user_id):
    """Retrieves an event."""
    return red.hgetall(_KEY_EVENT_USER.format(event_id, user_id))

def get_user_events(user_id, day):
    """Returns all the events for the user for the given day."""
    events = red.lrange(_KEY_EVENTS_USER_DAY.format(user_id, day), 0, -1)
    ret_events = []
    for event in events:
        tmp = get_event(event, user_id)
        if tmp is not None:
            ret_events.append(tmp)
    return ret_events
