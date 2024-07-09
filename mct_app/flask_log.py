from logging.config import dictConfig
from typing import Any

from flask import Flask

"""
We have options in python for stdout (streamhandling) and file logging
File logging has options for a Rotating file based on size or time (daily)
or a watched file, which supports logrotate style rotation
Most of the changes happen in the handlers, lets define a few standards
"""


class LogSetup(object):
    """Class for logging every event while app working."""

    def __init__(self, app=None, **kwargs: Any) -> None:
        """Contruct current app."""
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app: Flask) -> None:
        """Initialize of current app."""
        log_type = app.config['LOG_TYPE']
        logging_level = app.config['LOG_LEVEL']
        if log_type != 'stream':
            try:
                log_directory = app.config['LOG_DIR']
                app_log_file_name = app.config['APP_LOG_NAME']
                access_log_file_name = app.config['WWW_LOG_NAME']
            except KeyError as e:
                exit(code=f'{e} {log_type}')
            app_log = '/'.join([log_directory, app_log_file_name])
            www_log = '/'.join([log_directory, access_log_file_name])

        if log_type == 'stream':
            logging_policy = 'logging.StreamHandler'
        elif log_type == 'watched':
            logging_policy = 'logging.handlers.WatchedFileHandler'
        else:
            log_max_bytes = app.config['LOG_MAX_BYTES']
            log_copies = app.config['LOG_COPIES']
            logging_policy = 'logging.handlers.RotatingFileHandler'

        std_format = {
            'formatters': {
                'default': {
                    'format': '[%(asctime)s.%(msecs)03d]'
                    '%(levelname)s %(name)s:%(funcName)s: %(message)s',
                    'datefmt': '%d/%b/%Y:%H:%M:%S',
                },
                'access': {'format': '%(message)s'},
            }
        }
        std_logger = {
            'loggers': {
                '': {
                    'level': logging_level,
                    'handlers': ['default'],
                    'propagate': True},
                'app.access': {
                    'level': logging_level,
                    'handlers': ['access_logs'],
                    'propagate': False,
                },
                'root': {'level': logging_level, 'handlers': ['default']},
            }
        }
        if log_type == 'stream':
            logging_handler = {
                'handlers': {
                    'default': {
                        'level': logging_level,
                        'formatter': 'default',
                        'class': logging_policy,
                        'encoding': 'utf-8',
                    },
                    'access_logs': {
                        'level': logging_level,
                        'class': logging_policy,
                        'formatter': 'access',
                        'encoding': 'utf-8',
                    },
                }
            }
        elif log_type == 'watched':
            logging_handler = {
                'handlers': {
                    'default': {
                        'level': logging_level,
                        'class': logging_policy,
                        'filename': app_log,
                        'formatter': 'default',
                        'delay': True,
                        'encoding': 'utf-8',
                    },
                    'access_logs': {
                        'level': logging_level,
                        'class': logging_policy,
                        'filename': www_log,
                        'formatter': 'access',
                        'delay': True,
                        'encoding': 'utf-8',
                    },
                }
            }
        else:
            logging_handler = {
                'handlers': {
                    'default': {
                        'level': logging_level,
                        'class': logging_policy,
                        'filename': app_log,
                        'backupCount': log_copies,
                        'maxBytes': log_max_bytes,
                        'formatter': 'default',
                        'delay': True,
                        'encoding': 'utf-8',
                    },
                    'access_logs': {
                        'level': logging_level,
                        'class': logging_policy,
                        'filename': www_log,
                        'backupCount': log_copies,
                        'maxBytes': log_max_bytes,
                        'formatter': 'access',
                        'delay': True,
                        'encoding': 'utf-8',
                    },
                }
            }

        log_config = {
            'version': 1,
            'formatters': std_format['formatters'],
            'loggers': std_logger['loggers'],
            'handlers': logging_handler['handlers'],
            'encoding': 'utf-8',
        }
        dictConfig(log_config)
