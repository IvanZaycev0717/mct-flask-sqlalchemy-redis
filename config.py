import os
from enum import Enum, IntEnum, StrEnum

# Constants
ALLOWED_RUS_SYMBOLS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя -'
TIME_ZONE = 'Europe/Moscow'

# Paths
basedir = os.path.abspath(os.path.dirname(__file__))
CSV_FILE_PATH = os.path.join(basedir, 'csv', 'roles.csv')
FILE_BASE_PATH = os.path.join(basedir, 'mct_app', 'files')
FILE_REL_PATH = os.path.join('..', '..', '..', 'files')
LOGS_DIR_PATH = os.path.join(basedir, 'logs')
BANNED_IP_FILE_PATH = os.path.join(basedir, 'banned_ip', 'banned_ip.json')

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
    """Class for choosing the patient mood."""

    HAPPY = '😊Счастливый😊'
    IRRITATED = '😡Раздраженный😡'
    RELAXED = '😌Расслабленный😌'
    CONCERNED = '😟Обеспокоенный😟'
    RESTLESS = '😕Беспокойный😕'
    DISAPPOINTED = '😞Разочарованный😞'


class SocialPlatform(StrEnum):
    """Class for choosing social platform registering from."""

    GOOGLE = '(Google)'
    VK = '(VK)'
    ODNOKLASSNIKI = '(Odnoklassniki)'
    YANDEX = '(Yandex)'
    TELEGRAM = '(Telegram)'


# Config classes
class Config:
    """Main config for all the modes."""

    # General setup
    APP_NAME = os.environ.get('APP_NAME')
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # SQL Database setup
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQL_HOST = os.environ.get('SQL_HOST')
    SQL_PORT = os.environ.get('SQL_PORT')
    DATABASE = os.environ.get('DATABASE')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Banned IP path
    BANNED_IP_PATH = BANNED_IP_FILE_PATH

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Admin panel appearance
    FLASK_ADMIN_SWATCH = os.environ.get('FLASK_ADMIN_SWATCH')

    # Uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Ckeditor
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_FILE_UPLOADER = 'administration.upload'
    CKEDITOR_ENABLE_CSRF = True
    CKEDITOR_HEIGHT = 720

    # Google reCaptcha
    GOOGLE_RECAPTCHA_SITE_KEY = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY')
    GOOGLE_RECAPTCHA_SECRET_KEY = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY')

    # Redis Setup
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

    # Elasticsearch setup
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    # Logging Setup
    LOG_TYPE = 'file'
    LOG_LEVEL = 'WARNING'

    # File Logging Setup
    LOG_DIR = LOGS_DIR_PATH
    APP_LOG_NAME = 'app.log'
    WWW_LOG_NAME = 'www.log'
    LOG_MAX_BYTES = 100_000_000
    LOG_COPIES = 5

    # Caching
    CACHE_TYPE = 'RedisCache'
    CACHE_IGNORE_ERRORS = False
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')


class ProductionConfig(Config):
    """Class for app config on a real server in production."""

    # Modes
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False

    # Protection
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_ENABLED = True

    # Caching
    CACHE_IGNORE_ERRORS = True


class DevelopmentConfig(Config):
    """Class for app config while developing."""

    # Modes
    TESTING = False
    DEVELOPMENT = True
    DEBUG = True
    ASSETS_DEBUG = True
    DEBUG_TB_ENABLED = False

    # SQL
    SQLALCHEMY_RECORD_QUERIES = True

    # Protection
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_ENABLED = True


class TestingConfig(Config):
    """Class for app config while testing."""

    # Database setup
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')

    # Modes
    TESTING = True
    DEBUG = False
    DEVELOPMENT = False
    DEBUG_TB_ENABLED = False

    # Protection
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_ENABLED = False
