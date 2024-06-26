from http import HTTPStatus
from tests.conftest import expected_title

def test_site_pages_accessibility(client, site_url):
    response = client.get(site_url)
    assert response.status_code == HTTPStatus.OK, f'страница {site_url} недоступна'

def test_site_pages_title(client, site_url):
    response = client.get(site_url)
    assert bytes(
        expected_title, 'utf-8'
        ) in response.data, f'Заголовок title отсутсвует в {site_url}'