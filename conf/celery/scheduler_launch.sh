#!/bin/bash

/app/conf/django_secrets/inject_secrets.sh
celery -A boostress  beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=/app/logs/celery/scheduler.log