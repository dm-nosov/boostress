#!/bin/sh

# Copy static nginx config into place (no template substitution)
cp /app/conf/nginx/nginx.conf.template /etc/nginx/nginx.conf
exec "$@"