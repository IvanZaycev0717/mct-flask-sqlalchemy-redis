from http import HTTPStatus

from sqlalchemy import select
from tests.conftest import expected_title
from mct_app.auth.models import Role, User, UserRole
import os


def test_auth_pages_accessibility(client, auth_url):
    response = client.get(auth_url)
    assert response.status_code == HTTPStatus.OK, f'страница {auth_url} недоступна'

def test_auth_pages_title(client, auth_url):
    response = client.get(auth_url)
    assert bytes(
        expected_title, 'utf-8'
        ) in response.data, f'Заголовок title отсутсвует в {auth_url}'

def test_social_media_redirection(client, social_url):
    response = client.get(social_url)
    assert response.status_code in (HTTPStatus.FOUND, HTTPStatus.OK), f'страница {social_url} недоступна'

def test_registration(client, app):
    response = client.post('/registration', data={
        "password": "testpassword",
        "username": "testuser",
        "email": "test@test.ru"
        })

    with app.app_context():
        print(User.query.all())
        assert User.query.count() == 2
        assert response.status_code in (HTTPStatus.FOUND, HTTPStatus.OK), 'После регистрации страница недоступна'
        assert User.query.order_by(User.id.desc()).first().email == "test@test.ru"

def test_proba(client, app):
    with app.app_context():
        print(User.query.all())
        assert 1 == 1
