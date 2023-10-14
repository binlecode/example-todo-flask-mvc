from mvc.model import Todo, User, db
from mvc.auth import login_required

from threading import currentThread
from flask import Blueprint
from flask import Flask
from flask import flash
from flask import render_template
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from base64 import b64encode
from flask import current_app
import os

import logging

LOG = logging.getLogger(__name__)


bp = Blueprint("users", __name__)


@bp.route("/users", methods=["GET"])
def index():
    rs = User.query.all()
    user_list = [user for user in rs]
    # for user in rs:
    # t = {
    #     'id': user.id,
    #     'username': user.username
    # }
    # user_list.append(t)

    return render_template(
        "users/index.html", user_list=user_list, title="Todo App - Users"
    )


@bp.route("/users/add", methods=["POST"])
def add():
    username = request.form.get("username")
    password = request.form.get("password")
    password_check = request.form.get("password_check")

    error = None
    if not username:
        error = "Username is required"
    elif not password:
        error = "Password is required"
    elif password != password_check:
        error = "Password check faild"

    if error:
        flash(error)
        return redirect(url_for("users.index"))

    if User.query.filter_by(username=username).first() is not None:
        error = "User {} is already registered.".format(username)
        flash(error)
        return redirect(url_for("users.index"))

    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    flash(f"a user [{new_user.username}] was successfully added")
    return redirect(url_for("users.index"))


@bp.route("/users/update/<user_id>", methods=["POST", "PUT"])
def update(user_id):
    try:
        user = User.query.filter_by(id=user_id).first()
        new_username = request.form.get("username")
        if user:
            user.username = new_username
            db.session.commit()
        current_app.logger.debug(f">> user [{user.id}] was updated")
        flash(f"a user [{user.id}] was updated")
    except Exception as e:
        LOG.error(f"Failed to update user: {user}")
        LOG.error(e)
    return redirect(url_for("users.index"))


@bp.route("/users/delete/<user_id>", methods=["POST", "DELETE"])
def delete(user_id):
    user = User.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()
    flash(f"a user {user.id} was deleted")
    return redirect(url_for("users.index"))
