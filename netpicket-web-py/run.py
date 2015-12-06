# -*- coding: utf-8 -*-
"""
Run application
"""

from app import app
from gevent.pywsgi import WSGIServer
from werkzeug.serving import run_with_reloader

@run_with_reloader
def run():
    #WSGIServer(('', 5000), app).serve_forever()
    app.run(host='0.0.0.0', debug=True, port=5000)

if __name__ == '__main__':
    run()
