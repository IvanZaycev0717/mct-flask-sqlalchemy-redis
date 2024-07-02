import os

import pytest
from mimesis import Locale, Generic, random

from mct_app import create_app, db
from manage import general_setup

generic = Generic(locale=Locale.RU)

username = generic.person.username()
password = generic.person.password()
email = generic.person.email()
phone = generic.person.telephone()
content = generic.text.text()
title = generic.text.word()
last_update = generic.datetime.formatted_datetime(r'%Y-%m-%d %H:%M:%S')
image = generic.binaryfile.image()
sentence = generic.text.sentence()



@pytest.fixture(scope='session')
def app():
    app = create_app(mode=os.environ.get("APP_TEST_MODE"))
    with app.app_context():
        db.create_all()
        general_setup()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()

@pytest.fixture(scope='session', params=[
    '/admin/answer/',
    '/admin/articlecard/',
    '/admin/consultation/',
    '/admin/textbookchapter/',
    '/admin/diaryrecommendation/',
    '/admin/news/',
    '/admin/question/',
    '/admin/user/',
    '/admin/userdiary/',
    '/admin/userrole/',
    '/admin/usersession/',
    ])
def admin_url(client, request):
    return request.param

@pytest.fixture(scope='session', params=[
    '/',
    '/home',
    '/articles',
    '/textbook',
    '/questions',
    '/consultation',
    '/contacts',
    '/cookie-info'])
def site_url(client, request):
    return request.param


@pytest.fixture(scope='session', params=[
    'registration',
    'login',
    'reset-password'])
def auth_url(client, request):
    return request.param


@pytest.fixture(scope='session', params=[
    'google-login',
    'vk-login',
    'ok-login',
    'yandex-login'])
def social_url(client, request):
    return request.param


class AuthActions:    

    def __init__(self, client):
        self._client = client
        self._username = username
        self._password = password
        self._email = email
        self._phone = phone
    
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

class AdminActions:
    def __init__(self, client):
        self._client = client
        self._username = os.environ.get("ADMIN_NAME")
        self._password = os.environ.get("ADMIN_PASS")
        self._email = os.environ.get("ADMIN_EMAIL")

    def login(self):
        return self._client.post(
            '/login',
            data={
                'username': self._username,
                'password': self._password},
                follow_redirects=True
                )
    def logout(self):
        return self._client.get('/logout')


@pytest.fixture(scope='session')
def admin(client):
    return AdminActions(client)

@pytest.fixture(scope='session')
def auth(client):
    return AuthActions(client)

