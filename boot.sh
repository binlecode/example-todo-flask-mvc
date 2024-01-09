#!/bin/sh

# make sure to set LOG_LEVEL in container environment
exec gunicorn -b :5000 -w 2 --log-level=$LOG_LEVEL --access-logfile - --error-logfile - --worker-tmp-dir /dev/shm 'mvc:create_app()'
