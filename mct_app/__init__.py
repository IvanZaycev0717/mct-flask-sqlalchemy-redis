import os

from dotenv import load_dotenv
from flask import Flask, request, session, url_for
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail
from flask_ckeditor import CKEditor
from elasticsearch import Elasticsearch


load_dotenv()

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
mail = Mail()
login_manager = LoginManager()
admin = Admin(template_mode='bootstrap4')
ckeditor = CKEditor()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ.get('APP_SETTINGS'))
    app.app_context().push()
    CSRFProtect(app)

    # init app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app) 
    csrf.init_app(app)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None

    with app.app_context():
        db.create_all()

    from mct_app.auth.views import auth
    app.register_blueprint(auth)
    from mct_app.site.views import site
    app.register_blueprint(site)
    from mct_app.administration.views import administration
    app.register_blueprint(administration)
    from mct_app.administration.views import MyAdminIndexView
    admin.init_app(app, index_view=MyAdminIndexView())

    return app
