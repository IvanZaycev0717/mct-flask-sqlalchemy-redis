import os

from celery import shared_task
from flask import render_template
from flask_mailman import EmailMessage


@shared_task(ignore_result=True)
def send_email(recipient, subject, template, **kwargs):
    body = render_template(template + '.txt', **kwargs)
    msg = EmailMessage(subject, body, from_email=os.environ['MAIL_USERNAME'], to=[recipient])
    msg.send()

    
