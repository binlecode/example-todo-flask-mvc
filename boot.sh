#!/bin/sh
# set -b to bind to a specific ip address and port
# set --log-level to debug, info, warning, error, etc.
# set --access-logfile and --error-logfile with a -, which is stdout
# set -w 2 for 2 workers for less than or equal to 1 cpu core
# set -w to 2 * cpu cores + 1
# set -t to multiple threads enables thread pool in each worker process
# dont' set -t for less than 512MB memory
exec gunicorn -b :5000 -w 2 --log-level info --access-logfile - --error-logfile - --worker-tmp-dir /dev/shm 'mvc:create_app()'
