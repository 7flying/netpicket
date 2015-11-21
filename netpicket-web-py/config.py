# -*- coding: utf-8 -*-

import os
import uuid

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = str(uuid.uuid4())

# SQL Database stuff
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Redis DB stuff
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Google oauth
GOOGLE_LOGIN_CLIENT_ID = '25024647321-ch635ssha0lmo73lr24688slcb4mak4j.apps.googleusercontent.com'
GOOGLE_LOGIN_CLIENT_SECRET = os.environ['G_CLIENT_SECRET']
OAUTH_CREDENTIALS = {'google': {'id': GOOGLE_LOGIN_CLIENT_ID,
                                'secret': GOOGLE_LOGIN_CLIENT_SECRET}}

# Debugging
RANDOM_TIMELINE = True
