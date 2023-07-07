from mvc.model import Todo, User, db
from threading import currentThread
from flask import Blueprint
from flask import Flask
from flask import flash
from flask import render_template
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
from base64 import b64encode
from flask import current_app
import os

from sqlalchemy import desc

import logging

LOG = logging.getLogger(__name__)


bp = Blueprint("todos", __name__)


@bp.route("/todos", methods=["GET"])
def home():
    rs = Todo.query.order_by(desc(Todo.created_at)).all()
    # rs = Todo.query.all()
    todo_list = []
    for todo in rs:
        t = {
            "id": todo.id,
            "title": todo.title,
            "complete": todo.complete,
            "assignees": todo.assignees,
        }

        try:
            if todo.pic:
                t["img"] = b64encode(todo.pic).decode("utf-8")
        except Exception as e:
            current_app.logger.error("error transcoding image", e)

        todo_list.append(t)

    # transform blob to base64 for img tag data:uri
    # todo_list = [
    #     {
    #         'id': todo.id,
    #         'title': todo.title,
    #         'complete': todo.complete,
    #         'img': b64encode(todo.pic).decode("utf-8")
    #     } for todo in Todo.query.all()
    # ]

    # get all users as candidate assignees
    user_list = User.query.all()

    return render_template("todos/home.html", todo_list=todo_list, user_list=user_list)


@bp.route("/todos/add", methods=["POST"])
def add():
    title = request.form.get("title")

    file_err = None
    if "pic" not in request.files:
        file_err = "no file uploaded"
    else:
        file = request.files["pic"]
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == "":
            file_err = "no file selected for upload"
        else:
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                file_err = "bad file selected for upload"

    if file_err == None:
        # checking file size, memory efficiently
        # first try check browser content length if given
        if file.content_length:
            LOG.debug(f">> file content_length: {file.content_length}")
            if file.content_length > 1000000:
                file_err = "file size is too large: " + file.content_length
        else:
            # use seek and tell methods to get size without loading content
            # into memory
            pos = file.tell()
            file.seek(0, 2)  # seek to end
            size = file.tell()
            file.seek(pos)  # back to original position
            LOG.debug(f">> file size by seeking: {size}")
            if size > 1000000:
                # size_err = f'file size is too large: {size}'
                file_err = "file size is too large"

    new_todo = Todo(title=title, complete=False)
    assignee_ids = request.form.getlist("assignee_ids")
    assignees = User.query.filter(User.id.in_(assignee_ids)).all()
    new_todo.assignees = assignees

    if file_err:
        flash(file_err)
        LOG.warn(file_err)
        new_todo.pic = None
    else:
        LOG.debug(">> file is good, save to todo")
        blob = file.read()
        # todo: be careful not to read too much data into memory
        # this is not considerred safe to be used for size check
        # size = len(blob)
        new_todo.pic = blob

    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("todos.home"))


@bp.route("/todos/update/<todo_id>", methods=["POST", "PUT"])
def update(todo_id):
    try:
        todo = Todo.query.filter_by(id=todo_id).first()
        new_title = request.form.get("title")
        new_complete = bool(request.form.get("complete"))
        new_assignee_ids = request.form.getlist("assignee_ids")
        new_assignees = User.query.filter(User.id.in_(new_assignee_ids)).all()

        if todo:
            todo.title = new_title
            todo.complete = new_complete
            todo.assignees = new_assignees
            db.session.commit()
        current_app.logger.debug(f">> todo [{todo.id}] was updated")
        flash(f"a todo [{todo.id}] was updated")
    except Exception as e:
        LOG.error(f"Failed to update todo: {todo}")
        LOG.error(e)
    return redirect("/todos")


# @bp.route('/todos/delete/<int:todo_id>')
@bp.route("/todos/delete/<todo_id>", methods=["POST", "DELETE"])
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    flash("a todo was deleted")
    return redirect(url_for("todos.home"))
