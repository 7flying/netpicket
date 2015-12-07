# -*- coding: utf-8 -*-
"""
Holds the app's forms.
"""
from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, validators


class AddNetworkForm(Form):

    name = TextField('Network name', [validators.Length(min=1, max=30,
                                                        message='From 1 to 30 characters')])
    ipaddress = TextField("Buoy's IP address", [validators.IPAddress(
        message='IPv4 address')])
    submit = SubmitField('Save')
