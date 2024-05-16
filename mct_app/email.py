import os

from flask import render_template
from flask_mailman import EmailMessage

from mct_app import create_app



def send_email(recipient, subject, template, **kwargs):
    body = render_template(template + '.txt', **kwargs)
    msg = EmailMessage(subject, body, from_email=os.environ['MAIL_USERNAME'], to=[recipient])
    msg.send()
