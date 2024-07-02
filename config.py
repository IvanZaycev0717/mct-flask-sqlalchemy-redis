import os
from enum import Enum, IntEnum, StrEnum

# Constants
ALLOWED_RUS_SYMBOLS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя -'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Paths
basedir = os.path.abspath(os.path.dirname(__file__))
CSV_FILE_PATHS = {
    'roles': os.path.join(basedir, 'csv', 'roles.csv'),
}
FILE_BASE_PATH = os.path.join(basedir, 'mct_app', 'files')
FILE_REL_PATH = os.path.join('..', '..', '..', 'files')
IMAGE_BASE_PATH = {
    'news': os.path.join(
        basedir, 'mct_app', 'static', 'uploads', 'news'
        ),
    'articles': os.path.join(
        basedir, 'mct_app', 'static', 'uploads', 'articles'
        ),
    'textbook': os.path.join(
        basedir, 'mct_app', 'static', 'uploads', 'textbook'
        ),
}
IMAGE_REL_PATHS = {
    'news': os.path.join(
        '..', '..', '..', 'static', 'uploads', 'news'
        ),
    'articles': os.path.join(
        '..', '..', '..', 'static', 'uploads', 'articles'
        ),
    'textbook': os.path.join(
        '..', '..', '..', 'static', 'uploads', 'textbook'
        ),
}

TEST_DB_PATH = os.path.join(basedir, 'instance', 'pytest.db')
LOGS_DIR = os.path.join(basedir, 'logs')

# Links
SOICAL_MEDIA_LINKS = {
    'GitHub': r'https://github.com/IvanZaycev0717/mct-flask-sqlalchemy-redis',
    'YouTube': r'https://www.youtube.com/@IvanZaycev_0717',
    'Telegram': r'https://t.me/ivanzaycev0717',
    'WhatsApp': r'https://www.whatsapp.com/?lang=ru_RU'
}

# Enum classes
class Is(IntEnum):
    """Class of digits for a current role."""

    ADMIN = 1
    CONTENT_MANAGER = 2
    DOCTOR = 3
    PATIENT = 4


class Mood(Enum):
    HAPPY = '😊Счастливый😊'
    IRRITATED = '😡Раздраженный😡'
    RELAXED = '😌Расслабленный😌'
    CONCERNED = '😟Обеспокоенный😟'
    RESTLESS = '😕Беспокойный😕'
    DISAPPOINTED = '😞Разочарованный😞'


class SocialPlatform(StrEnum):
    GOOGLE = '(Google)'
    VK = '(VK)'
    ODNOKLASSNIKI = '(Odnoklassniki)'
    YANDEX = '(Yandex)'
    TELEGRAM = '(Telegram)'


# Config classes
class Config:
    APP_NAME = os.environ.get('APP_NAME')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('PASS_2')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    FLASK_ADMIN_SWATCH = os.environ.get('FLASK_ADMIN_SWATCH')
    UPLOAD_FOLDER = os.path.join(
        basedir, 'mct_app', 'static', 'uploads', 'news'
        )
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_FILE_UPLOADER = 'administration.upload'
    CKEDITOR_ENABLE_CSRF = True
    CKEDITOR_HEIGHT = 720
    GOOGLE_RECAPTCHA_SITE_KEY = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY')
    GOOGLE_RECAPTCHA_SECRET_KEY = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    # Logging Setup
    LOG_TYPE = "file"
    LOG_LEVEL = "WARNING"

    # File Logging Setup
    LOG_DIR = LOGS_DIR
    APP_LOG_NAME = "app.log"
    WWW_LOG_NAME = "www.log"
    LOG_MAX_BYTES = 100_000_000
    LOG_COPIES = 5


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    TESTING = False
    DEVELOPMENT = True
    DEBUG = True
    ASSETS_DEBUG = True
    DEBUG_TB_ENABLED = True
    SQLALCHEMY_RECORD_QUERIES = True
    WTF_CSRF_CHECK_DEFAULT = True


class TestingConfig(Config):
    DEBUG_TB_ENABLED = False
    TESTING = True
    DEBUG = False
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
