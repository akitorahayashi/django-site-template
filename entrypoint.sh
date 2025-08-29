#!/bin/sh

set -eu

if [ "$#" -eq 0 ] || [ "$1" = "gunicorn" ]; then
    count=0
    echo "Waiting for database to be ready..."
    
    until pg_isready -h db -p 5432 -U ${POSTGRES_USER}; do
        count=$((count + 1))
        if [ ${count} -ge 30 ]; then
            echo "Failed to connect to database after 30 attempts. Exiting."
            exit 1
        fi
        echo "Waiting for database to be ready... (${count}/30)"
        sleep 1
    done
    echo "Database is ready."

    echo "Checking if database exists and creating if necessary..."
    if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DEV_DB_NAME}'" | grep -q 1; then
        echo "Creating database ${POSTGRES_DEV_DB_NAME}..."
        PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE \"${POSTGRES_DEV_DB_NAME}\";" || true
    fi
    echo "Database exists."

    echo "Applying database migrations..."
    python manage.py migrate
    echo "Database migrations completed successfully."
fi

if [ "$#" -gt 0 ]; then
    exec "$@"
else
    WORKERS=${NUM_OF_GUNICORN_WORKERS:-1}
    echo "Starting Gunicorn server with ${WORKERS} worker(s)..."
    exec gunicorn config.wsgi:application --bind "0.0.0.0:8000" --workers "${WORKERS}"
fi
