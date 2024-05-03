from http import HTTPStatus

import pytest
from mct_app import create_app

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        'TESTING': True
    })
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_home(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK, 'Главная страница недоступна'
    
    response = client.get('/home')
    assert response.status_code == HTTPStatus.OK, 'Главная страница недоступна'

def test_news(client):
    response = client.get('/news')
    assert response.status_code == HTTPStatus.OK, 'Страница новостей недоступна'