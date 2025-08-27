#!/bin/sh

# このスクリプトは、コンテナのCMDとして渡されたコマンドを実行します。
# exec "$@" を使用することで、渡されたコマンドがコンテナのPID 1として実行され、
# シグナル（例: docker stopからのSIGTERM）を正しく受信できるようになります。

# Ensure the virtual environment is on the PATH
export PATH="/opt/venv/bin:$PATH"

set -eu

# Collect static files if required
if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start the main process
echo "Starting Gunicorn server..."
exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000
