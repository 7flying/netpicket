# -*- coding: utf-8 -*-

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail

app = Flask(__name__, static_url_path='')
Bootstrap(app)
app.config.from_object('config')

# Mail extension

mail = Mail(app)

import views, errorviews, email
