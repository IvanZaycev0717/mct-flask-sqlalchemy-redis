from datetime import datetime
import json
import logging
import os

from celery import Celery, Task
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from flask import abort, Flask, request, Response, session
from flask_admin import Admin
from flask_caching import Cache
from flask_ckeditor import CKEditor
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mailman import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import pytz
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from mct_app.flask_log import LogSetup

load_dotenv()


class Base(DeclarativeBase):
    """Class for using SQLAlchemy 2.0 as declarative language."""

    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    })


db = SQLAlchemy(model_class=Base)
mail = Mail()
login_manager = LoginManager()
admin = Admin(template_mode='bootstrap4')
ckeditor = CKEditor()
csrf = CSRFProtect()
toolbar = DebugToolbarExtension()
cache = Cache()


def create_app(mode=os.environ.get('APP_DEV_MODE')) -> Flask:
    """Create Flask app using application factory pattern."""
    app = Flask(__name__)

    # config setUp
    app.config.from_object(mode)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.environ.get('BROKER_URL'),
            result_backend=os.environ.get('RESULT_BACKEND'),
            task_ignore_results=True,
            broker_connection_retry_on_startup=True,
            broker_transport_options={
                'visibility_timeout': 3600,
                'fanout_prefix': True,
                'fanout_patterns': True,
                'max_connections': 1,
                'password': os.environ.get('REDIS_PASSWORD')
            }
        ),
    )
    # Jinja2 filters
    app.jinja_env.filters['datetimefilter'] = datetimefilter

    # Configure app to get a real IP of visitor
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1)

    # init app
    CSRFProtect(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    toolbar.init_app(app)
    app.elasticsearch = Elasticsearch(
        os.environ.get('ELASTICSEARCH_URL')) \
        if os.environ.get('ELASTICSEARCH_URL') else None
    app.config.from_prefixed_env()
    celery_init_app(app)
    LogSetup().init_app(app)
    cache.init_app(app)

    # create database
    with app.app_context():
        db.create_all()

    # check whether visitor is banned
    @app.before_request
    def check_ip_in_blacklist() -> None:
        current_ip = request.remote_addr
        banned_ip_path = app.config.get('BANNED_IP_PATH')
        if os.path.exists(banned_ip_path):
            with open(banned_ip_path) as file:
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
    def after_request(response: Response) -> Response:
        """Do logging after every request."""
        logger = logging.getLogger('app.access')
        logger.info(
            '%s [%s] %s %s %s %s %s %s %s',
            request.remote_addr,
            datetime.now().strftime('%d/%b/%Y:%H:%M:%S.%f')[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            request.user_agent,
        )
        return response

    cache.clear()
    return app


def celery_init_app(app: Flask) -> Celery:
    """Initialize celery app."""
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config['CELERY'])
    celery.set_default()
    app.extensions['celery'] = celery

    return celery


def datetimefilter(value, format='%d.%m.%Y в %H:%M'):
    """Show date on a template as DAY.MONTH.YEAR HOURS:MINUTES."""
    tz = pytz.timezone('Europe/Moscow')
    utc = pytz.timezone('UTC')
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)
