# -*- coding: utf-8 -*-

import redis, sys
if 'threading' in sys.modules:
    del sys.modules['threading']
import gevent
from gevent import monkey
monkey.patch_all()

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager


app = Flask(__name__, static_url_path='')
Bootstrap(app)
app.config.from_object('config')

# SQl Alchemy
db = SQLAlchemy(app)

# Redis
red = redis.StrictRedis(host=app.config['REDIS_HOST'],
                        port=app.config['REDIS_PORT'],
                        db=app.config['REDIS_DB'])

# Login extension
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.init_app(app)

# Mail extension

mail = Mail(app)

import views, errorviews, email, auth, models, const
