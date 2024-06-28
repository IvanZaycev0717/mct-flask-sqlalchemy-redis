from http import HTTPStatus
import os
from mct_app.auth.models import User


def test_admin_was_created(app, admin):
    with app.app_context():
        user = User.query.first()
        assert user is not None, 'Админ не бьл создан'
        assert user.username == admin._username, 'Имя админа не соответсвует'
        assert user.email == admin._email, 'Почта админа не соответсвует'

def test_admin_success_login(app, admin):
    response = admin.login()

    with app.app_context():
        assert bytes('Приветствуем,', 'utf-8') in response.data, 'Админ не перенесен в личный кабинет'

def test_admin_has_access_to_admin_panel(app, client):
    response = client.get('/admin')
    final_response = client.get(response.headers['Location'])

    with app.app_context():
        assert final_response.status_code == HTTPStatus.OK, 'Админ не может войти в админку'

def test_admin_pages_accessibility(client, app, admin_url):
    response = client.get(admin_url)

    with app.app_context():
        assert response.status_code == HTTPStatus.OK, f'страница {response} недоступна'

def test_admin_success_logout(app, admin):
    response = admin.logout()

    with app.app_context():
        assert response.headers["Location"] == '/', 'После logout админ не переходит на главную страницу'

def test_auth_user_hasnt_access_to_admin_panel(app, auth, client):
    auth.login()

    response = client.get('/admin')
    final_response = client.get(response.headers['Location'])

    with app.app_context():
        assert final_response.status_code == HTTPStatus.FORBIDDEN, 'Простой пользователь вошел в админку'
    
    auth.logout()

def test_anon_hasnt_access_to_admin_panel(app, client):
    response = client.get('/admin')
    final_response = client.get(response.headers['Location'])

    with app.app_context():
        assert final_response.status_code == HTTPStatus.FORBIDDEN, 'Аноним вошел в админку'
