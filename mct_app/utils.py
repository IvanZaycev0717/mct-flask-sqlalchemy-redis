import uuid
import re
from typing import Dict, List, Tuple
from config import ALLOWED_RUS_SYMBOLS
from mct_app.site.models import ArticleCard
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

def get_images_names(text: str) -> List[str]:
    pattern = r'<img[^>]*src="/files/([^"]+)"[^>]*>'
    return re.findall(pattern, text)


def get_statistics_data(statistics: Dict[int, bool]) -> int:
    hundred_percent = len(statistics)
    done_percent = len(
        [value for value in statistics.values() if value is True]
        )
    return int(done_percent*100/hundred_percent)

def get_textbook_chapters_paragraphs(chapters_paragraphs: List[Tuple[str]]) -> Dict[str, List[str]]:
    textbook_data = {}
    for item in chapters_paragraphs:
        chapter = item[0]
        paragraph = item[1]
        if chapter not in textbook_data:
            textbook_data[chapter] = [paragraph]
        else:
            textbook_data[chapter].append(paragraph)
    return textbook_data

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
