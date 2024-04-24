from flask import Blueprint
from mct_app.auth.models import User, db

auth = Blueprint('auth', __name__)

