from mct_app.utils import generate_image_name, get_random_email, get_images_names, get_statistics_data, is_russian_name_correct
import pytest
from tests.test_site import first_name, last_name, phone

_test_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test HTML for Regular Expression</title>
</head>
<body>
    <img src="/files/image1.jpg" alt="Image 1">
    <img src="/files/image2.png" alt="Image 2">
    <img src="/files/image3.gif" alt="Image 3">
    <img src="/images/image4.jpg" alt="Image 4">
    <img src="/files/image5.jpeg" alt="Image 5">
</body>
</html>
"""

def test_generate_image_name():
    result = generate_image_name()
    assert result.startswith('image'), 'Сгенерированное название картинки не начинается с image'

def test_get_random_email():
    result = get_random_email()
    assert result.endswith('@metacognitive.ru'), 'Неверно сгенерирован случайный email'

def test_get_image_names():
    result = get_images_names(_test_html)
    assert result == ['image1.jpg', 'image2.png', 'image3.gif', 'image5.jpeg'], 'Неверное регулярное выражение для функции get_images_names'

@pytest.mark.parametrize(('statistics', 'output'), (
        ({1: True, 2: False, 3: True, 4: True, 5: False}, 60),
        ({1: False, 2: False, 3: False}, 0),
        ({}, 0),
        ({1: True, 2: True, 3: True}, 100)))
def test_get_statistics_data(statistics, output):
    result = get_statistics_data(statistics)
    assert result == output, f'Неверно рассичтана статистика для {statistics}'

@pytest.mark.parametrize(('name', 'output'), ((first_name, True), (last_name, True), (phone, False)))
def test_is_russian_name_correct(name, output):
    result = is_russian_name_correct(name)
    assert result == output, f'Неверная валидация русского имени для {name}'















