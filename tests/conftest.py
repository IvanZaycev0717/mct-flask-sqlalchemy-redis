import os

import pytest
from mimesis import Generic, Locale


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
    """Create a test application fixture."""
    app = create_app(mode=os.environ.get('APP_TEST_MODE'))
    with app.app_context():
        db.create_all()
        general_setup()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    """Create test application client fixture."""
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
    '/admin/usersession/',])
def admin_url(request):
    """Return all the urls of admin panel."""
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
def site_url(request):
    """Return all the urls of the site section."""
    return request.param


@pytest.fixture(scope='session', params=[
    'registration',
    'login',
    'reset-password'])
def auth_url(request):
    """Return all the urls of the auth section."""
    return request.param


@pytest.fixture(scope='session', params=[
    'google-login',
    'vk-login',
    'ok-login',
    'yandex-login'])
def social_url(request):
    """Return all the urls of the social media platforms."""
    return request.param


class AuthActions:
    """Class to create authenticated user and his actions."""

    def __init__(self, client):
        """Initialize attributes of authenticated user."""
        self._client = client
        self._username = username
        self._password = password
        self._email = email
        self._phone = phone

    def register(self):
        """Reginsten random user on the website."""
        return self._client.post('/registration', data={
            'username': self._username, 'password': self._password,
            'email': self._email, 'phone': self._phone},
            follow_redirects=True)

    def login(self):
        """Login registered user on the website."""
        return self._client.post(
            '/login',
            data={'username': self._username, 'password': self._password},
            follow_redirects=True)

    def logout(self):
        """Logout registered user on the website."""
        return self._client.get('/logout')


class AdminActions:
    """Class to create admin and his actions."""

    def __init__(self, client):
        """Initialize attributes of authenticated user."""
        self._client = client
        self._username = os.environ.get('ADMIN_NAME')
        self._password = os.environ.get('ADMIN_PASS')
        self._email = os.environ.get('ADMIN_EMAIL')

    def login(self):
        """Login admin on the website."""
        return self._client.post(
            '/login',
            data={'username': self._username, 'password': self._password},
            follow_redirects=True)

    def logout(self):
        """Logout admin on the website."""
        return self._client.get('/logout')


@pytest.fixture(scope='session')
def admin(client):
    """Create admin fixture."""
    return AdminActions(client)


@pytest.fixture(scope='session')
def auth(client):
    """Create authenticated user fixture."""
    return AuthActions(client)
