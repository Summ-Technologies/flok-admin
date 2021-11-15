#!/bin/bash
gunicorn server:app -w 2 -b 0.0.0.0:8001 --log-config /app/logging.conf ${EXTRA_GUNICORN_ARGS} --daemon
nginx
tail -f /logs/*