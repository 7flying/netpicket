# -*- coding: utf-8 -*-

from app import app
from gevent.pywsgi import WSGIServer


#app.run(host='0.0.0.0', debug=True, port=5000)
WSGIServer(('', 5000), app).serve_forever()
