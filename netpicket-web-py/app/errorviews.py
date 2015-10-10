# -*- coding: utf-8 -*-

from flask import render_template
from app import app

@app.errorhandler(401)
def unauthorished(e):
    return render_template('http_error.html', code=401, desc='Unauthorised',
                           lmessage='You need to log in.')
@app.errorhandler(403)
def forbidden(e):
    return render_template('http_error.html', code=403, desc='Forbidden',
                           lmessage='You are forbidden to access this.')
@app.errorhandler(404)
def page_not_found(e):
    return render_template('http_error.html', code=404, desc='Page Not found',
                           lmessage='What you were looking for is not here')
