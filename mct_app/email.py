import os

from flask import render_template
from flask_mail import Message

from mct_app import create_app
from mct_app import mail


def send_email(recipient, subject, **kwargs):
    app = create_app()
    app.config.from_object(os.environ.get('APP_SETTINGS'))
    app.app_context().push()
    with app.app_context():
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipient=[recipient])
        msg.body = f'Отправлено {kwargs}'
        mail.send(msg)
