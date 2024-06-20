import os

from celery import shared_task
from celery.contrib.abortable import AbortableTask
from flask import render_template
from flask_mailman import EmailMessage



@shared_task(bind=True, base=AbortableTask)
def send_email(self, recipient, subject, template, **kwargs):
    body = render_template(template + '.txt', **kwargs)
    msg = EmailMessage(subject, body, from_email=os.environ['MAIL_USERNAME'], to=[recipient])
    if self.is_aborted():
        return 'Письмо не отправлено'
    msg.send()
