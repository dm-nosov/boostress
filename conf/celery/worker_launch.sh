#!/bin/bash

/app/conf/django_secrets/inject_secrets.sh
celery -A boostress  worker -l INFO --logfile=./logs/celery/worker.log