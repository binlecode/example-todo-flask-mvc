# todos mvc: classic mvc web stack

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
# run flask app
export FLASK_APP=mvc
FLASK_DEBUG=true python -m flask run
```

The flask app can also run with gunicorn, a production grade web container.

```sh
gunicorn -b :5000 -w 2 --access-logfile - --error-logfile - 'mvc:create_app()'
```


## container deployment




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

## MVC Implementations:

- MVC stack, html templates and sqlalchemy orm
- Sementic-UI is used for page styles
- Save a web uploaded file to a BLOB db column

To run in dev mode,
first, install python environment,

Debug and reloader are enabled by development env.
And reloader is enabled when debug is enabled.
To enable debug in a non-dev env:

```sh
export FLASK_DEBUG=1
```

To run in terminal shell model:

```sh
python -m flask shell
```

to run in gunicorn for a production like env

```sh
pip install gunicorn
# set sync worker count to 4
gunicorn -b localhost:8000 -w 4 'mvc:create_app()'
```

build docker image:

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

## todo_rest_sql app

This todo app is REST only, no web html UI.

Also, this app uses raw sql executions for cruds.

App structure follows: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

App structure:

```
todo_rest_sql
|- __init__.py: package bootstrap
|- db.py: database config and bootstrap
|- schema.sql: DDL for db.py to initialize
|- routes.py: routes and actions
|- todos_app.py: main app entry for flask run
|- todos_rest_sql.db: sqlite3 db file
```

Run this at the project root folder level:

```sh
export FLASK_APP=todos_app.py
export FLASK_ENV=development
flask init-db
flask run
```

No need to re-run 'init-db' for successive runs unless a db reset is needed.
