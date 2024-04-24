import os

from dotenv import load_dotenv
from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase


load_dotenv()

class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(model_class=Base)
db.init_app(app)

migrate = Migrate(app, db)

from mct_app.site.views import site
app.register_blueprint(site)
from mct_app.auth.views import auth
app.register_blueprint(auth)

with app.app_context():
    db.create_all()
