#!/bin/sh

# Function to safely read and clean secret
read_secret() {
    secret_file="$1"
    # Read file, remove any control characters, and trim whitespace
    cat "$secret_file" | tr -d '\000-\037' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

# Read secrets
SECRET_KEY=$(read_secret /run/secrets/django_secret_key)
DB_PASSWORD=$(read_secret /run/secrets/postgres_password)
ADMIN_PASSWORD=$(read_secret /run/secrets/admin_password)

# Create or overwrite the file with the initial comment
cat <<EOF > /app/boostress/local_settings.py
# This file is auto-generated. Do not edit manually.
SECRET_KEY = "${SECRET_KEY}"
DB_PASSWORD = "${DB_PASSWORD}"
ADMIN_PASSWORD = "${ADMIN_PASSWORD}"
EOF

exec "$@"