#!/bin/sh
# set --access-logfile and --error-logfile with a -, which is stdout
# set -w 2 for 2 workers for less than or equal to 1 cpu core
# usually set -w to 2 * cpu cores + 1
# dont' set -t for less than 512MB memory
# set -t to multiple threads per process enables thread pool in each 
# worker process, which requires more memory
exec gunicorn -b :5000 -w 2 --access-logfile - --error-logfile - --worker-tmp-dir /dev/shm 'mvc:create_app()'
