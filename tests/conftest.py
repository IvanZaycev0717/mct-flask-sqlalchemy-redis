import os
import pytest
from mct_app import create_app, db

expected_title = "<title>Метакогнитивная терапия - новости, статьи, учебник, консультации</title>"

@pytest.fixture()
def app():
    app = create_app()
    app.config.from_object(os.environ.get('APP_TEST_MODE'))
    with app.app_context():
        db.create_all()
    yield app

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
    'google-login', 'vk-login', 'ok-login', 'ok-redirect', 'yandex-login'])
def social_url(client, request):
    return request.param
