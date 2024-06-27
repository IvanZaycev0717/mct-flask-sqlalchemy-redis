import os

import pytest
from mimesis import Locale, Generic, random

from mct_app import create_app, db
from manage import general_setup

random.global_seed = 0xFF
generic = Generic(locale=Locale.RU)
expected_title = "<title>Метакогнитивная терапия - новости, статьи, учебник, консультации</title>"

@pytest.fixture(scope='session')
def app():
    app = create_app(mode=os.environ.get("APP_TEST_MODE"))
    with app.app_context():
        db.create_all()
        general_setup()
    
    yield app


@pytest.fixture(scope='session')
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


class AuthActions:
    def __init__(self, client):
        self._client = client
        self._username = generic.person.username()
        self._password = generic.person.password()
        self._email = generic.person.email()
        self._phone = generic.person.telephone()
    
    def register(self):
        return self._client.post('/registration', data={
            'username': self._username, 'password': self._password,
            'email': self._email, 'phone': self._phone},
            follow_redirects=True
            )
    
    def login(self):
        return self._client.post('/login', data={'username': self._username, 'password': self._password}, follow_redirects=True)

    def logout(self):
        return self._client.get('/logout')

@pytest.fixture(scope='session')
def auth(client):
    return AuthActions(client)




        
    

