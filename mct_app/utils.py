import re
from typing import Dict, List
import uuid

from flask import json
from config import ALLOWED_RUS_SYMBOLS, BANNED_IP_FILE
from mct_app.site.models import ArticleCard
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def get_images_names(text: str) -> List[str]:
    """Return all the images links from HTML body."""
    pattern = r'<img[^>]*src="/files/([^"]+)"[^>]*>'
    return re.findall(pattern, text)


def get_random_email() -> str:
    """Generate a random email address for social registration."""
    return f'{uuid.uuid4()}@metacognitive-therapy.ru'


def get_statistics_data(statistics: Dict[int, bool]) -> int:
    """Return percentage of content completion."""
    full_amount = len(statistics)
    done_amount = len(
        [value for value in statistics.values() if value is True])
    if full_amount != 0:
        return int(done_amount * 100 / full_amount)
    return 0


def generate_image_name(obj, file_data) -> str:
    """Generate a random picture name."""
    image_suffix = uuid.uuid4()
    return secure_filename(f"image_{image_suffix}")


def get_articles_by_months(article_cards: List[ArticleCard]) -> dict[str, str]:
    """Create a dictionary of articles by month and year."""
    acticles_by_month = {}
    for time, article_id, title in article_cards:
        head = f'{get_month_in_russian(time.strftime('%B'))} {time.year}'
        if head not in acticles_by_month:
            acticles_by_month[head] = {title: article_id}
        else:
            acticles_by_month[head].update({title: article_id})
    return acticles_by_month


def resize_image(
        image: Image,
        max_width: int = 1280,
        max_height: int = 720) -> Image:
    """Resize any uploading image to proper condition."""
    width, height = image.size
    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(height * (max_width / width))
        else:
            new_height = max_height
            new_width = int(width * (max_height / height))

        resized_image = image.resize((new_width, new_height))
        return resized_image
    return image


def save_image_as_webp(
        image: FileStorage,
        path: str,
        format: str = 'WEBP') -> None:
    """Save image on SSD as WEBP format."""
    image = Image.open(image)
    if format == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')
    elif image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA')

    image = resize_image(image)

    with open(path, 'wb') as fp:
        image.save(fp, format, quality=100, method=3)


def is_russian_name_correct(name: str) -> bool:
    """Check correctness of russian name."""
    name = name.lower()
    for letter in name:
        if letter not in ALLOWED_RUS_SYMBOLS:
            return False
    return True


def get_month_in_russian(month: str) -> str:
    """Convert English months names into Russian."""
    match month:
        case 'January': return 'Январь'
        case 'February': return 'Февраль'
        case 'March': return 'Март'
        case 'April': return 'Апрель'
        case 'May': return 'Май'
        case 'June': return 'Июнь'
        case 'July': return 'Июль'
        case 'August': return 'Август'
        case 'September': return 'Сентябрь'
        case 'October': return 'Октябрь'
        case 'November': return 'Ноябрь'
        case 'December': return 'Декабрь'


def save_banned_ip_file(banned_ip: str) -> None:
    """Write and overwrite banned IPs into JSON file."""
    with open(BANNED_IP_FILE, 'w') as file:
        json.dump(banned_ip, file)
