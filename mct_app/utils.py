import uuid
import re
from typing import Dict, List, Tuple

from flask import Flask
from config import ALLOWED_RUS_SYMBOLS
from mct_app.site.models import ArticleCard
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from celery import Celery, Task

def get_images_names(text: str) -> List[str]:
    pattern = r'<img[^>]*src="/files/([^"]+)"[^>]*>'
    return re.findall(pattern, text)



def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def get_statistics_data(statistics: Dict[int, bool]) -> int:
    full_amount = len(statistics)
    done_amount = len(
        [value for value in statistics.values() if value is True]
        )
    return int(done_amount*100/full_amount)

def generate_image_name(obj, file_data):
    image_suffix = uuid.uuid4()
    return secure_filename(f"image_{image_suffix}")

def get_articles_by_months(article_cards: List[ArticleCard]) -> dict:
    acticles_by_month = {}
    for time, article_id, title in article_cards:
        head = f'{time.strftime('%B')} {time.year}'
        if head not in acticles_by_month:
            acticles_by_month[head] = {title: article_id}
        else:
            acticles_by_month[head].update({title: article_id})
    return acticles_by_month


def resize_image(
        image: Image,
        max_width: int = 1280,
        max_height: int = 720) -> Image:
    width, height = image.size

    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(height * (max_width / width))
        else:
            new_height = max_height
            new_width = int(width * (max_height/ height))

        resized_image = image.resize((new_width, new_height))
        return resized_image
    return image


def save_image_as_webp(
        image: FileStorage,
        path: str,
        format: str = 'WEBP') -> None:
    image = Image.open(image)
    if format == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')
    elif image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA')

    image = resize_image(image)

    with open(path, 'wb') as fp:
        image.save(fp, format, quality=100, method=3)


def is_russian_name_correct(name: str) -> bool:
    name = name.lower()
    for letter in name:
        if letter not in ALLOWED_RUS_SYMBOLS:
            return False
    return True
