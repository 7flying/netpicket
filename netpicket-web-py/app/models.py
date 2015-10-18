# -*- coding: utf-8 -*-

from app import db, rd


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

# --- User-id --- #

def get_user_id(user):
    pass

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


