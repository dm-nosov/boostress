#!/bin/sh

./conf/django_secrets/inject_secrets.sh
celery -A boostress  beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=./logs/celery/scheduler.log