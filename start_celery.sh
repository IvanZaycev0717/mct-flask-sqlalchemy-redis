#!/bin/sh

celery -A manage.celery worker --loglevel=info