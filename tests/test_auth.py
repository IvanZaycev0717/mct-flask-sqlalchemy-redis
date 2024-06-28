from http import HTTPStatus

import pytest


from tests.conftest import username, password, email, generic

from mct_app.auth.models import User

expected_title = "<title>Метакогнитивная терапия - новости, статьи, учебник, консультации</title>"


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
    assert response.status_code == HTTPStatus.FOUND, f'страница {social_url} недоступна'

def test_successful_registration(app, auth, admin):
    response = auth.register()

    with app.app_context():
        user = User.query.order_by(User.id.desc()).first()
        assert User.query.count() == 2, 'Пользователь не зарегистрировался'
        assert bytes('Приветствуем,', 'utf-8') in response.data, 'Зарегистрированный пользователь не перенесен в личный кабинет'
        assert user.username == auth._username, 'Имя пользователя не совпадает'
        assert user.email == auth._email, 'Почта пользователя не совпадает'
        assert user.phone == auth._phone, 'Телефон пользователя не совпадает'


def test_new_user_roles(app):
    with app.app_context():
        user: User = User.query.order_by(User.id.desc()).first()
        assert user.is_admin() is False, 'Новый пользователь не может быть админом'
        assert user.is_content_manager() is False, 'Новый пользователь не может быть контент-менеджером'
        assert user.is_doctor() is False, 'Новый пользователь не может быть доктором'
        assert user.is_patient() is True, 'Новый пользователь должен быть пациентом'
        assert user.is_anonymous is False, 'После регистрации пользователь не может быть анонимным'

def test_logout(app, client, auth):
    response = auth.logout()

    with app.app_context():
        assert response.headers["Location"] == '/', 'После logout не пользователь не переходит на главную страницу'

@pytest.mark.parametrize(
        ('username', 'password', 'email', 'message'),
        (('', generic.person.password(), generic.person.email(), bytes('Требуется ввести имя пользователя', 'utf-8')),
        (generic.person.username(), '', generic.person.email(), bytes('Требуется ввести пароль', 'utf-8')),
        (generic.person.username(), generic.person.password(), '', bytes('Требуется ввести адрес электронной почты', 'utf-8')),
        (generic.person.username(), generic.person.password(), generic.person.username(), bytes('Неверно введён адрес электронной почты', 'utf-8')),
        (username + "(", generic.person.password(), generic.person.email(), bytes('недоупстимы', 'utf-8')),
        (generic.person.username() + ')', generic.person.password(), generic.person.email(), bytes('недоупстимы', 'utf-8')),
        ('(' + generic.person.username() + ')', generic.person.password(), generic.person.email(), bytes('недоупстимы', 'utf-8')),
        ))
def test_empty_fields_registration(client, app, username, password, email, message):
    response = client.post('/registration', data={'username': username, 'password': password, 'email': email})

    with app.app_context():
        assert message in response.data, f'Не было выведено {message}'



@pytest.mark.parametrize(
        ('username', 'password', 'email', 'message'),
        ((username, password, generic.person.email(), bytes('Пользователь с таким именем уже существует', 'utf-8')),
        (generic.person.username(), password, email, bytes('Такой адрес электронной почты уже существует', 'utf-8'))
        ))
def test_user_already_exists_registration(app, client, username, password, email, message):
    response = client.post('/registration', data={'username': username, 'password': password, 'email': email})

    with app.app_context():
        assert message in response.data, f'Не было выведено {message}'

def test_successful_login(app, auth):
    response = auth.login()

    with app.app_context():
        assert bytes('Приветствуем,', 'utf-8') in response.data, 'Зарегистрированный пользователь не перенесен в личный кабинет'

@pytest.mark.parametrize(
        ('username', 'password', 'message'),
        (('', password, bytes('Требуется ввести имя пользователя', 'utf-8')),
        (username, '', bytes('Требуется ввести пароль', 'utf-8'))))
def test_empty_fields_login(app, auth, client, username, password, message):
    auth.logout()
    response = client.post('/login', data={'username': username, 'password': password})

    with app.app_context():
        assert message in response.data, f'Не было выведено {message}'

@pytest.mark.parametrize(
        ('email', 'message'),
        (('',  bytes('Требуется ввести адрес электронной почты', 'utf-8')),
        (username, bytes('Неверно введён адрес электронной почты', 'utf-8'))
        ))
def test_incorrect_reset_password(app, client, email, message):
    response = client.post('/reset-password', data={'email': email})

    with app.app_context():
        assert message in response.data, f'Не было выведено {message}'

def test_auth_user_has_statistics_access(app, auth, client):
    auth.login()
    response = client.get(f'/profile/{username}/statistics')

    with app.app_context():
        assert bytes('Изученные статьи:', 'utf-8') in response.data, 'Пользователь не получил доступ к статистике'

def test_auth_user_has_diary_access(app, client):
    response = client.get(f'/profile/{username}/diary')

    with app.app_context():
        assert bytes('Новая запись', 'utf-8') in response.data, 'Пользователь не получил доступ к дневнику'

@pytest.mark.parametrize(('user_url'), (('admin'), (username)))
def test_anon_user_hasnt_statistics_access(app, auth, client, user_url):
    auth.logout()
    response = client.get(f'/profile/{user_url}/statistics')

    with app.app_context():
        assert response.status_code == HTTPStatus.UNAUTHORIZED, 'Анонимный пользователь не должен был получить доступ к статистике'

@pytest.mark.parametrize(('user_url'), ('admin', username))
def test_anon_user_hasnt_diary_access(app, client, user_url):
    response = client.get(f'/profile/{user_url}/diary')

    with app.app_context():
        assert response.status_code == HTTPStatus.UNAUTHORIZED, 'Анонимный пользователь не должен был получить доступ к дневнику'

def test_admin_has_access_to_user_diary(app, client, admin):
    admin.login()
    response = client.get(f'/profile/{username}/diary')

    with app.app_context():
        assert response.status_code == HTTPStatus.OK, 'Админ не имеет доступа к статистике пользователя'
















