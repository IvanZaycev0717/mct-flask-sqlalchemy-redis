from http import HTTPStatus
import os
from config import IMAGE_BASE_PATH
from mct_app.auth.models import User
from mct_app.site.models import TextbookChapter, TextbookParagraph
from tests.conftest import title, sentence, generic, last_update, image
from mct_app.administration.views import CustomImageUploadField, generate_image_name
from wtforms.validators import DataRequired

new_title = generic.text.quote()


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

def test_admin_can_create_textbook_chapter(app, client):
    client.post('/admin/textbookchapter/new/', data={
        "name": title,
        "description": sentence
    })

    with app.app_context():
        chapter: TextbookChapter = TextbookChapter.query.first()
        assert chapter is not None, 'Новый раздел учебника не был создан'
        assert chapter.name == title, 'Название нового раздела учебника не совпадает'
        assert chapter.description == sentence, 'Описание нового раздела учебника не совпадает'

def test_admin_sent_empty_textbook_chapter_fields(app, client):
    response = client.post('/admin/textbookchapter/new/', data={
        "name": "",
    })

    with app.app_context():
        assert b'This field is required.' in response.data, 'Был создан раздел учебника с пустым названием'


def test_admin_can_edit_textbook_chapter(app, client):
    response = client.post(f'/admin/textbookchapter/edit/?id={1}&url=/admin/textbookchapter/', data={
        'name': new_title
    })

    with app.app_context():
        chapter: TextbookChapter = TextbookChapter.query.first()
        assert chapter is not None, 'Отредактированный раздел учебника не существует'
        assert chapter.name == new_title, 'Отредактированный заголовок раздела учебника не изменился'
        assert chapter.description == sentence, 'Отредактированное описание учебника изменилось'

def test_admin_can_delete_textbook_chapter(app, client):
    client.post('/admin/textbookchapter/delete/', data={
        "id": 1
    })

    with app.app_context():
        chapter: TextbookChapter = TextbookChapter.query.first()
        assert chapter is None, 'Новый раздел не был удален'



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
