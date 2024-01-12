# __init__.py
#
# The __init__.py serves double duty:
# - it tells Python that the mvc directory is a package
# - it contains the application factory
#

import datetime
import logging
import os
import time

from flask import Flask, g, render_template, request, session
from flask.helpers import make_response

from config import Config
from mvc.model import User, db


def create_app(config=Config):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(config)

    # setup logging
    # check if flask app is served by gunicorn
    if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
        app.logger.info("flask app is served by gunicorn")
        # overwrite the default logger to use gunicorn logger
        # Get the Gunicorn logger
        gunicorn_logger = logging.getLogger("gunicorn.error")
        # Overwrite the default logger to use Gunicorn logger
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
        app.logger.info(
            f"flask app logger is overwritten to use gunicorn logger: {gunicorn_logger}"
        )
        app.logger.info(
            f"flask app logger level: {logging.getLevelName(app.logger.level)}"
        )
    else:
        app.logger.info("flask app is served by flask buit-in server")
        app.logger.setLevel(app.config["LOG_LEVEL"])
        app.logger.info(
            f"flask app logger level: {logging.getLevelName(app.logger.level)}"
        )

    # setup db conn and initialize db
    db.init_app(app)
    with app.app_context():
        app.logger.info("sqlalchemy started database sync")
        # for any schema DDL change, need to enable db.drop_all() to reset db
        # db.drop_all()
        db.create_all()
        app.logger.info("sqlalchemy completed database sync")

    # setup background tasks with celery
    from .celery_init import celery_init_app
    from .celery_tasks import CELERY_BEAT_SCHEDULE

    app.config.from_mapping(
        CELERY=dict(
            # Use redis as the broker for celery
            # "redis://localhost:6379/0"
            broker_url="redis://localhost",
            # set redis as backend to store the task state and return values
            result_backend="redis://localhost",
            # set default not to store task state and result in redis, but can
            # override specific tasks to enable it
            task_ignore_result=True,
            # optional: set a prefix for all keys stored in redis by this app
            result_backend_transport_options={"global_keyprefix": "todos_mvc_"},
            # add a beat schedule for periodic tasks
            beat_schedule=CELERY_BEAT_SCHEDULE,
        ),
    )
    # This is the celery app that will be used in `celery -A' command,
    # its full name is `flask_app.app.celery_app` for -A option
    celery_init = celery_init_app(app)
    app.logger.info("flask app loaded with celery")

    # initialize blueprints

    from . import home

    app.register_blueprint(home.bp)

    from . import todos

    app.register_blueprint(todos.bp)

    from . import users

    app.register_blueprint(users.bp)

    from . import auth

    app.register_blueprint(auth.bp)

    # app.add_url_rule('/', endpoint='index')

    # add global logging middleware

    # use before_request interceptor to load g context

    @app.before_request
    def log_req_and_get_start_time():
        app.logger.debug("before_request > get_req_start_time")

        # timestamp = rfc3339(dt, utc=True)
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        host = request.host.split(":", 1)[0]
        args = dict((k, request.args.getlist(k)) for k in request.args.keys())
        form = dict((k, request.form.getlist(k)) for k in request.form.keys())

        log_details = {
            "method": request.method,
            "path": request.path,
            "ip": ip,
            "host": host,
            "params": args,
            "form": form,
        }

        request_id = request.headers.get("X-Request-ID")
        if request_id:
            log_details["request_id"] = request_id

        if request.form:
            log_details["request_form"] = request.form.to_dict()

        # log request details
        # request.args is of MultiDict type, need to getlist from each key
        # app.logger.debug('request args:')
        # for k in request.args.keys():
        #     app.logger.debug(f' > {k} : {request.args.getlist(k)}')
        # request.form is MultiDict type too
        # app.logger.debug('request.form:')
        # for k in request.form.keys():
        #     app.logger.debug(f' > {k} : {request.form.getlist(k)}')

        app.logger.debug(">> request :: " + str(log_details))

        g.start = time.time()

    # we can have multiple interceptors, they are executed in the order
    # they are defined

    @app.before_request
    def load_logged_in_user():
        app.logger.debug("before_request > load_logged_in_user")
        # try to fetch session user
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            # this could return none
            g.user = User.query.filter_by(id=user_id).first()
        app.logger.debug(f"getting g.user: {g.user}")

    @app.after_request
    def log_resp(response):
        if request.path == "/favicon.ico":
            return response
        elif request.path.startswith("/static"):
            return response

        now = time.time()
        duration = round(now - g.start, 2)
        dt = datetime.datetime.fromtimestamp(now)
        # timestamp = rfc3339(dt, utc=True)
        log_details = {"status": response.status_code, "duration": duration, "time": dt}
        app.logger.debug(">> response :: " + str(log_details))

        return response

    # errorhandler 404 needs to registered outside of blueprint
    # because a blueprint is not aware of the entire route mapping

    @app.errorhandler(404)
    def err_not_found(error):
        app.logger.info("server returns 404")
        app.logger.info(error)
        resp = make_response(render_template("error404.html"), 404)
        # todo: can decorate resp object here
        return resp

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def err_internal_server_error(error):
        app.logger.error("server returns 500")
        app.logger.error(error)
        resp = make_response(render_template("error500.html", error=error), 500)
        return resp

    # todo: impl custom 403 and 401 error after login is added

    return app
