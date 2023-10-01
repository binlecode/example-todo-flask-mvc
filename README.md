# todos application mvc web stack with flask

This application provides basic implementation examples for:

- application factory pattern
  - `create_app()` function in `mvc/__init__.py`
- web stack:
  - blueprint for app routes
  - MVC stack, jinja2 html templates
  - sqlalchemy orm
  - web file upload save to BLOB db column
  - basic username/password authentication with Werkzeug security
- UI:
  - Sementic-UI is used for page styles
- background job:
  - celery + redis
  - see [`README_celery_redis.md`](./README_celery_redis.md)
- deployment:
  - gunicorn as wsgi server
  - docker container

## local run

Check Dockerfile for container runtime setup.

For a local run:

```sh
pyenv shell 3.10
# create and activate venv
python -m venv venv
source venv/bin/activate
# install dependencies
pip install -U pip
pip install -r requirements.txt
```

Run flask app with debug enabled.
Auto-reload is enabled when debug is enabled.

```sh
FLASK_APP=mvc FLASK_DEBUG=true python -m flask run
```

To run in terminal shell model:

```sh
FLASK_DEBUG=1 FLASK_APP=mvc python -m flask shell
```

Flask shell is useful for interactive debugging.

```python
# in shell, check global variables
dir()
['Todo', 'User', '__builtins__', 'app', 'db', 'g']
# check app context
app
<Flask 'mvc'>

# explicitly create an orm session and query the model
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=db.engine)
session = Session()
# this returns a list of model instance objects
session.query(User).all()

# User.__table__ is the table metadata object for the User model
# this returns list of tuples (row data)
session.query(User.__table__).all()

# use metadata to reflect db schema to fetch table metadata object
from sqlalchemy import MetaData
db_metadata = MetaData()
db_metadata.reflect(bind=db.engine)
# get the table metadata object
todos_tb = db_metadata.tables["todos"]
print(todos_tb_metadata)
# the table metadata object is the internal orm mapping object used in
# query, which is the same as the User.__table__ object
session = Session()
print(session.query(todos_tb).all())
```

## background job with celery + redis

## deployment

For deployment, flask app uses gunicorn as a production grade wsgi server.

```sh
gunicorn -b :5000 -w 2 --access-logfile - --error-logfile - 'mvc:create_app()'
```

For container deployment, use docker to build image:

```sh
docker build -t todosmvc-flask .
# check built image
docker images
```

run container:

```sh
docker run --name todomvc-flask -p 5000:5000 --rm todosmvc-flask
# add -d in detached mode
docker run --name todomvc-flask -d -p 5000:5000 --rm todosmvc-flask
```

container server is at http://127.0.0.1:5000/todos

## project dependency setup

```sh
# create .python-version file with v3.10
pyenv shell 3.10
# venv is natively supported in python v3.4+
python -m venv venv
# activate venv:
source venv/bin/activate
pip install -U pip
# install pkgs
pip install -U flask flask-sqlalchemy python-dotenv toml gunicorn
# update requirements file
pip freeze > requirements.txt
```
