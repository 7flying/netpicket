# -*- coding: utf-8 -*-

from flask import render_template

from app import app



@app.route('/', methods=['GET', 'POST'])
def main_page():
    """ """
    return render_template('index.html')
