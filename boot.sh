#!/bin/sh
# set --access-logfile and --error-logfile with a -, which is stdout
# set -w 2 for 2 workers, set to 4 workers for a more concurrent need
exec gunicorn -b :5000 -w 2 --access-logfile - --error-logfile - 'mvc:create_app()'
