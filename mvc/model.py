# model.py
#

import uuid

import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from sqlalchemy.orm import backref, validates
from sqlalchemy.sql import func

db = SQLAlchemy()

# this the m-to-m mapping table b/t todos and users
# an m-to-m mapping table should not be a model, but simply a table
assignments = db.Table(
    "assignments",
    db.Column(
        "todo_id", db.String(length=36), db.ForeignKey("todos.id"), primary_key=True
    ),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)

# to check table DDL for Todo model, in flask console, run Todo.__table__


class Todo(db.Model):
    # flask-sqlalchemy sets table name to be the lower-camel-case of class name
    # it would be 'todo' for this entity
    # we would like to set the table name to be plural, aka 'todos'
    __tablename__ = "todos"

    # auto timestamping
    # use sqlalchemy's func.now() to ask DB to calculate the timestamp itself
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    # created_at = db.Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    # id = db.Column(db.Integer, primary_key=True)
    # use uuid as pk, use lambda to define an id generator
    id = db.Column(
        "id", db.String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    pic = db.Column(db.LargeBinary, nullable=True)

    assignees = db.relationship(
        "User",
        secondary=assignments,
        lazy="subquery",
        backref=db.backref("todos", lazy="subquery"),
    )

    def __repr__(self):
        return "<Todo {}>".format(self.title)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return "<User {}>".format(self.username)
