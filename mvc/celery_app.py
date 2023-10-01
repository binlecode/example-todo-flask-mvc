# with flask factory pattern, celery_app is not available in module namespace
# To use celery commands, create a celery_app.py file that calls the Flask app
# factory and gets the Celery app from the returned Flask app.

from . import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]

# to run worker process, point the celery command to this file.

# celery -A mvc.celery_app worker --loglevel INFO
# celery -A mvc.celery_app beat --loglevel INFO
