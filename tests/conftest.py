import os
from flask_sqlalchemy import SQLAlchemy
import pytest
from mct_app import Base, create_app, db
from mct_app.auth.views import logout
from manage import general_setup

expected_title = "<title>Метакогнитивная терапия - новости, статьи, учебник, консультации</title>"

@pytest.fixture()
def app():
    app = create_app(os.environ.get("TEST_DATABASE_URL"))
    app.config.update({
        "WTF_CSRF_CHECK_DEFAULT": False,
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
    general_setup()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(params=[
    '/', '/home', '/articles', 'textbook', 'questions',
    'consultation', 'contacts', 'cookie-info'])
def site_url(client, request):
    return request.param

@pytest.fixture(params=[
    'registration', 'login', 'reset-password'])
def auth_url(client, request):
    return request.param

@pytest.fixture(params=[
    'google-login', 'vk-login', 'ok-login', 'yandex-login'])
def social_url(client, request):
    return request.param
