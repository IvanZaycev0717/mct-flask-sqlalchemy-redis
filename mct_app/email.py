import os

from flask import render_template
from flask_mailman import EmailMessage

from mct_app import create_app
from mct_app import mail



def send_email(recipient, subject, **kwargs):
    msg = EmailMessage('hello', 'Body of email', from_email=os.environ['MAIL_USERNAME'], to=[recipient])
    msg.send()
