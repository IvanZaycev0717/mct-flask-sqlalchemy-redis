from http import HTTPStatus

from tests.conftest import generic
from tests.test_auth import expected_title

first_name = generic.person.first_name()
last_name = generic.person.last_name()
phone = generic.person.telephone()


def test_site_pages_accessibility(client, site_url):
    """Test all the site pages have an access."""
    response = client.get(site_url)
    assert response.status_code == HTTPStatus.OK, \
        f'страница {site_url} недоступна'


def test_site_pages_title(client, site_url):
    """Test all the site pages have the same title."""
    response = client.get(site_url)
    assert bytes(expected_title, 'utf-8') in response.data, \
        f'Заголовок title отсутсвует в {site_url}'


def test_unexisted_page_access(app, client):
    """Test 404 error for unexisted page."""
    random_url = generic.person.phone_number()
    response = client.get(random_url)

    with app.app_context():
        assert response.status_code == HTTPStatus.NOT_FOUND, \
            f'Отстствует ошибка 404 для {random_url}'
