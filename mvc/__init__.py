# __init__.py
#
# The __init__.py serves double duty:
# - it tells Python that the mvc directory is a package
# - it contains the application factory
#
# this todos app is following app-factory/blueprint pattern
# app-factory prevents app from being a global variable, and also helps
# creating app for test environment
#

from mvc.model import User
from flask.helpers import make_response
from flask import render_template
from flask import Flask
from flask import g, request, session
import os
import logging
import time
import datetime
import json

# LOG = logging.getLogger(__file__)
# LOG.setLevel(logging.DEBUG)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # secret key will be used for securely signing the session cookie
    # app.config['SECRET_KEY'] = 'todo-dev-secret'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./todos.db'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config is None:
        # load default config.py from project root
        # app.config.from_object('config')

        # load config.py from current folder, if exists
        try:
            from . import config

            app.config.from_object(config)
        except Exception as e:
            app.logger.error(f"ERROR loading config: {e}")

        # load instance/config.py file
        # when instance_relative_config=True is set in Flask() call
        # slient=True to mute error if file not found in instance folder
        app.config.from_pyfile("config.py", silent=True)

    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # /// = relative path, //// = absolute path

    # setup db conn
    from mvc.model import db

    db.init_app(app)

    # initialize db
    app.logger.info("sqlalchemy started database sync")
    with app.app_context():
        # for any schema DDL change, need to enable db.drop_all() to reset db
        # db.drop_all()
        db.create_all()
    app.logger.info("sqlalchemy completed database sync")

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
        app.logger.error("server returns 404")
        resp = make_response(render_template("error404.html"), 404)
        # todo: can decorate resp object here
        return resp

    # todo: impl custom 500 error handler

    # todo: impl custom 403 and 401 error after login is added

    return app
