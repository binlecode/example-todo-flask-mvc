import logging
import os
import time
from base64 import b64encode
from threading import currentThread

from flask import Blueprint, Flask, current_app, flash, redirect, request, url_for
from werkzeug.utils import secure_filename

from mvc.model import Todo, db

LOG = logging.getLogger(__name__)

# get system startup time
start_time = time.time()


bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    return "Hello, Todos MVC App with Flask!"


@bp.route("/health")
def health_check():
    return "System up and running for {%d} seconds" % (get_uptime())


@bp.route("/appinfo", methods=["GET"])
def get_app_info():
    """
    Returns the application information.
    """

    # build map between url map rules and view functions by endpoint
    url_map_rules = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint in current_app.view_functions:
            view_function = current_app.view_functions[rule.endpoint]
            # add module name to view function name to aovid name conflict
            view_function_name = f"{view_function.__module__}.{view_function.__name__}"
        else:
            view_function_name = None

        url_map_rules.append({"rule": str(rule), "view_function": view_function_name})

    # build map between error code and error handler
    # if the key is None, it means the error handler is defined for the
    # whole application, not the current blueprint
    # this is because each blueprint can have its own error handlers
    error_handler_spec = {}
    for key, value in current_app.error_handler_spec.items():
        if key is None:
            key = "application"
        error_handler_spec[key] = list(value.keys())

    return dict(
        name=current_app.name,
        db=current_app.config["SQLALCHEMY_DATABASE_URI"],
        blueprints=[name for name, bp in current_app.blueprints.items()],
        url_map_rules=url_map_rules,
        error_handler_spec=error_handler_spec,
    )


def get_uptime():
    """
    Returns the number of seconds since the program started.
    """
    # do return startTime if you just want the process start time
    return time.time() - start_time
