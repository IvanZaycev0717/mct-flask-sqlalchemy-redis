#!/bin/sh

export FLASK_APP=manage

flask db init

flask db migrate

flask db upgrade

pytest

gunicorn -w 4 -c gunicorn_config.py manage:app