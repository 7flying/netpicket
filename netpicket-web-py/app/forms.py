# -*- coding: utf-8 -*-
"""
Holds the app's forms.
"""
from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, SelectField, SelectMultipleField,\
     validators
import app.models as models

class AddNetworkForm(Form):

    name = TextField('Network name', [validators.Length(min=1, max=30,
                                                        message='From 1 to 30 characters')])
    ipaddress = TextField("Buoy's IP address", [validators.IPAddress(
        message='IPv4 address'), validators.Required()])
    submit = SubmitField('Save')

def get_network_options(user_id):
    """Returns the available networks for a given user."""
    options = []
    for network  in models.get_user_networks(user_id):
        options.append((network['id'], network['name']))
    return options

class AddCALEntryForm(Form):

    mac = TextField('MAC address', [validators.MacAddress(),
                                    validators.Required()])
    networks = SelectMultipleField('Select one or more networks',
                                   [validators.Required()])
    type = SelectField('Select the entry type', [validators.Required()],
                       choices=[('B', 'Black list'), ('W', 'White list')])
    submit = SubmitField('Save')

    @classmethod
    def new(cls, user_id):
        """
        To dynamically update the available values in the 'networks'
        SelectMultipleField we need to populate the values from the DB.
        """
        form = cls()
        form.networks.choices = get_network_options(user_id)
        return form
