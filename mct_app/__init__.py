from datetime import datetime
import logging
import os
import json


from dotenv import load_dotenv
from flask import Flask, abort, request, session, url_for
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail
from flask_ckeditor import CKEditor
from elasticsearch import Elasticsearch
from celery import Celery, Task
from flask_debugtoolbar import DebugToolbarExtension
from mct_app.flask_log import LogSetup
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
mail = Mail()
login_manager = LoginManager()
admin = Admin(template_mode='bootstrap4')
ckeditor = CKEditor()
csrf = CSRFProtect()
toolbar = DebugToolbarExtension()
cache = Cache()

def create_app(mode=os.environ.get('APP_SETTINGS')):
    app = Flask(__name__)

    # config setUp
    app.config.from_object(mode)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.environ.get('BROKER_URL'),
            result_backend=os.environ.get('RESULT_BACKEND'),
            task_ignore_results=True,
            broker_connection_retry_on_startup=True
        ),
    )

    # Configure app to get a real IP of visitor
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # init app
    CSRFProtect(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    toolbar.init_app(app)
    app.elasticsearch = Elasticsearch(
        os.environ.get('ELASTICSEARCH_URL')
        ) if os.environ.get('ELASTICSEARCH_URL') else None
    app.config.from_prefixed_env()
    celery_init_app(app)
    LogSetup().init_app(app)
    cache.init_app(app)

    # create database
    with app.app_context():
        db.create_all()
    
    # check whether visitor is banned
    @app.before_request
    def check_ip_in_blacklist():
        current_ip = request.remote_addr
        banned_ip_path = app.config.get('BANNED_IP_PATH')
        if os.path.exists(banned_ip_path):
            with open(banned_ip_path) as  file:
                blacklist = json.load(file)
            if current_ip in blacklist:
                cache.clear()
                session.clear()
                abort(403)

    # register blueprints
    from mct_app.auth.views import auth
    app.register_blueprint(auth)
    from mct_app.site.views import site
    app.register_blueprint(site)
    from mct_app.administration.views import administration
    app.register_blueprint(administration)
    from mct_app.administration.views import MyAdminIndexView
    admin.init_app(app, index_view=MyAdminIndexView())

    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        logger = logging.getLogger("app.access")
        logger.info(
            "%s [%s] %s %s %s %s %s %s %s",
            request.remote_addr,
            datetime.now().strftime("%d/%b/%Y:%H:%M:%S.%f")[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            request.user_agent,
        )
        return response

    return app

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery
