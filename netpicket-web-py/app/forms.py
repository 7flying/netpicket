# -*- coding: utf-8 -*-
"""
Holds the app's forms.
"""
from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, SelectField, SelectMultipleField,\
     validators
import app.models as models

class AddNetworkForm(Form):

    name = TextField('Network name',
                     [validators.Length(min=1, max=30,
                                        message='From 1 to 30 characters.')],
                     description='Display name.')
    ipaddress = TextField("Buoy's IP address", [validators.IPAddress(
        message='IPv4 address required.'), validators.Required()],
        description='IP address of the buoy which will scan the network.')
    submit = SubmitField('Save')

def get_network_options(user_id):
    """Returns the available networks for a given user."""
    options = []
    for network in models.get_user_networks(user_id):
        options.append((network['id'], network['name']))
    return options

class AddCALEntryForm(Form):

    mac = TextField('MAC address', [validators.MacAddress(),
                                    validators.Required()],
                    description='MAC address of the target host.')
    networks = SelectMultipleField('Select one or more networks')
    type = SelectField('Select the entry type',
                       choices=[('B', 'Black list'), ('W', 'White list')])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(AddCALEntryForm, self).__init__(*args, **kwargs)

    @classmethod
    def new(cls, user_id):
        """
        To dynamically update the available values in the 'networks'
        SelectMultipleField we need to populate the values from the DB.
        """
        form = cls()
        form.networks.choices = get_network_options(user_id)
        return form

class AddHostForm(Form):

    name = TextField('Host name',
                     [validators.Length(min=1, max=30,
                                        message='From 1 to 30 characters.')],
                     description='Display name.')
   # mac = TextField('MAC address', [validators.MacAddress(),
   #                                 validators.Required()])
    services = TextField('Services to monitor',
                         [validators.Length(min=1, max=140,
                                            message='From 1 to 140 characters.')],
                         description="""Comma separated values.
                         Please choose meaningful names like
                         'Firefox' and 'Nginx'.""")
    submit = SubmitField('Save')
