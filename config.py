import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()

    # Flask’s SECRET_KEY configuration value to protect its forms abd cookies.
    # Flask-WTF extension also uses it to protect web forms against CSRF.
    SECRET_KEY = os.environ.get("SECRET_KEY", "you-can-not-guess")

    # if database url is not set by env var, use sqlite as default
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "todos.db")

    # enable query sql printout
    SQLALCHEMY_ECHO = True
    # Flask-SQLAlchemy has its own event notification system that gets layered
    # on top of SQLAlchemy. It tracks modifications to the SQLAlchemy session.
    # This costs extra resources.
    # Suggest disabling it if not in use to save system resources.
    # Set the option SQLALCHEMY_TRACK_MODIFICATIONS to enables/disables the
    # modification tracking system.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # set global max request size, including file upload
    MAX_CONTENT_LENGTH = 1024 * 1024
    # limit upload file extensions
    UPLOAD_EXTENSIONS = [".jpg", ".png", ".gif"]
