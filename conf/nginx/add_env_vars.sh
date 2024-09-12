#!/bin/sh

# Temporary location to process template
TEMP_DIR=$(mktemp -d)
TEMP_FILE="$TEMP_DIR/nginx.conf"

# Copy template to temp location
cp /app/conf/nginx/nginx.conf.template "$TEMP_FILE"

# Perform find-and-replace using sed
sed -i "s/{{VIRTUAL_HOST}}/${VIRTUAL_HOST}/g" "$TEMP_FILE"

# Move the processed file to the nginx config directory
mv -f "$TEMP_FILE" /etc/nginx/nginx.conf

# Clean up temp directory
rm -rf "$TEMP_DIR"

exec "$@"