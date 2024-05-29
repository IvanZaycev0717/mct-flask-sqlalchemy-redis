from typing import List
from mct_app.site.models import ArticleCard
from config import Months
from PIL import Image
from werkzeug.datastructures import FileStorage


def get_articles_by_months(article_cards: List[ArticleCard]) -> dict:
    acticles_by_month = {}
    for time, article_id, title in article_cards:
        head = f'{Months(time.month).name} {time.year}'
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
