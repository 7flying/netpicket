#-*- coding: utf-8 -*-
"""
WSGI entry point for Gunicorn.
gunicorn --bind unix:<socket-name>.sock -k gevent wsgi:app &
"""
from app import app

if __name__ == "__main__":
    app.run()
