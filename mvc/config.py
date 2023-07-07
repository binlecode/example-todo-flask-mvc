import os

basedir = os.path.abspath(os.path.dirname(__file__))


SECRET_KEY = "todo-dev-secret"

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
    basedir, "todos.db"
)

# enable query sql printout
SQLALCHEMY_ECHO = True

# Flask-SQLAlchemy has its own event notification system that gets layered on top of SQLAlchemy.
# To do this, it tracks modifications to the SQLAlchemy session. This takes extra resources, so
# the option SQLALCHEMY_TRACK_MODIFICATIONS enables/disables the modification tracking system.
# Suggest disabling it if not in use to save system resources.
# To turn off the Flask-SQLAlchemy event system (and disable the warning):
SQLALCHEMY_TRACK_MODIFICATIONS = False

# set global max request size, including file upload
MAX_CONTENT_LENGTH = 1024 * 1024
# limit upload file extensions
UPLOAD_EXTENSIONS = [".jpg", ".png", ".gif"]
