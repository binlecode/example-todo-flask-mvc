#!/bin/sh
# set --access-logfile and --error-logfile with a -, which is stdout
# set -w 2 for 2 workers, set -t 2 for 2 threads per worker
exec gunicorn -b :5000 -w 2 -t 2 --access-logfile - --error-logfile - 'mvc:create_app()'
