import os
from enum import IntEnum, StrEnum, Enum


basedir = os.path.abspath(os.path.dirname(__file__))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

CSV_FILE_PATHS = {
    'roles': os.path.join(basedir, 'csv', 'roles.csv'),
}

FILE_BASE_PATH = os.path.join(basedir, 'mct_app', 'files')
FILE_REL_PATH = os.path.join('..', '..', '..', 'files')

IMAGE_BASE_PATH = {
    'news': os.path.join(basedir, 'mct_app', 'static', 'uploads', 'news'),
    'articles': os.path.join(basedir, 'mct_app', 'static', 'uploads', 'articles'),
    'textbook': os.path.join(basedir, 'mct_app', 'static', 'uploads', 'textbook'),
}

IMAGE_REL_PATHS = {
    'news': os.path.join('..', '..', '..', 'static', 'uploads', 'news'),
    'articles': os.path.join('..', '..', '..', 'static', 'uploads', 'articles'),
    'textbook': os.path.join('..', '..', '..', 'static', 'uploads', 'textbook'),
}


SOICAL_MEDIA_LINKS = {
    'GitHub': r'https://github.com/IvanZaycev0717/mct-flask-sqlalchemy-redis',
    'YouTube': r'https://www.youtube.com/@IvanZaycev_0717',
    'Telegram': r'https://t.me/ivanzaycev0717',
    'WhatsApp': r'https://www.whatsapp.com/?lang=ru_RU'
}


class Is(IntEnum):
    ADMIN = 1
    CONTENT_MANAGER = 2
    DOCTOR = 3
    PATIENT = 4


class SocialPlatform(StrEnum):
    GOOGLE = '(Google)'
    VK = '(VK)'
    ODNOKLASSNIKI = '(Odnoklassniki)'
    YANDEX = '(Yandex)'
    TELEGRAM = '(Telegram)'


class Config:
    APP_NAME = os.environ.get('APP_NAME')
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('PASS_2')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    FLASK_ADMIN_SWATCH = os.environ.get('FLASK_ADMIN_SWATCH')
    UPLOAD_FOLDER = os.path.join(basedir, 'mct_app', 'static', 'uploads', 'news')
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_FILE_UPLOADER = 'administration.upload'
    CKEDITOR_ENABLE_CSRF = True
    CKEDITOR_HEIGHT = 720
    GOOGLE_RECAPTCHA_SITE_KEY = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY')
    GOOGLE_RECAPTCHA_SECRET_KEY = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY')
    
    


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True


class TestingConfig(Config):
    TESTING = True
