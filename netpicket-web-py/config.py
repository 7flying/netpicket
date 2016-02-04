# -*- coding: utf-8 -*-

import os
import uuid

basedir = os.path.abspath(os.path.dirname(__file__))

TESTING = False

SECRET_KEY = str(uuid.uuid4())

# SQL Database stuff
DATABASE_NAME = os.environ.get('DB_NAME', 'apptestmysql')
_DB_USER = os.environ.get('DB_USER', 'netpicketdb')
_DB_PASS = os.environ.get('DB_PASS', 'toor')
_DB_HOST = os.environ.get(
    'DB_HOST', 'netpicketdb.cc4qjaigxmw1.eu-west-1.rds.amazonaws.com:3306')

if TESTING:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://' + _DB_USER + ':' +  _DB_PASS + \
      '@' + _DB_HOST +'/' + DATABASE_NAME + '?charset=utf8'

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Redis DB stuff
if TESTING:
    REDIS_HOST = 'localhost'
else:
    REDIS_HOST = 'netpicketcluster.snik29.0001.euw1.cache.amazonaws.com'
REDIS_PORT = 6379
REDIS_DB = 0

# Google oauth
GOOGLE_LOGIN_CLIENT_ID = '25024647321-ch635ssha0lmo73lr24688slcb4mak4j.apps.googleusercontent.com'
GOOGLE_LOGIN_CLIENT_SECRET = os.environ['G_CLIENT_SECRET']
OAUTH_CREDENTIALS = {'google': {'id': GOOGLE_LOGIN_CLIENT_ID,
                                'secret': GOOGLE_LOGIN_CLIENT_SECRET}}

# Debugging
RANDOM_TIMELINE = False
