# -*- coding: utf-8 -*-

from flask.ext.mail import Message
from app import app, mail

def send_email(to, subject, template):
    """Sends an email"""
    mess = Message(subject, recipients=[to], html=template,
                   sender=app.config['MAIL_DEFAULT_SENDER'])
    mail.send(mess)
