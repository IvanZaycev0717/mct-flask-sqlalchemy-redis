import os
from enum import IntEnum

basedir = os.path.abspath(os.path.dirname(__file__))

CSV_FILE_PATHS = {
    'roles': os.path.join(basedir, 'csv', 'roles.csv'),
    'roles_permissions': os.path.join(basedir, 'csv', 'roles_permissions.csv'),
    'permissions': os.path.join(basedir, 'csv', 'permissions.csv')
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


class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True