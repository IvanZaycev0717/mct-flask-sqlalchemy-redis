import os
from typing import Any

from celery import shared_task
from flask import render_template
from flask_mailman import EmailMessage


@shared_task(ignore_result=True)
def send_email(recipient: str,
               subject: str,
               template: str, **kwargs: Any) -> None:
    """Send email by means of message broker and Celery."""
    body = render_template(template + '.txt', **kwargs)
    msg = EmailMessage(
        subject,
        body,
        from_email=os.environ['MAIL_USERNAME'], to=[recipient])
    msg.send()
