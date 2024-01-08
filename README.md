# todos application mvc web stack with flask

This application includes:

- application factory pattern, in `mvc.__init__.py`
  - prevents app from being a global variable
  - supports creating multiple app instances for background jobs context,
    test environment context, etc.
  - see:
    - https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/
    - https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure
- mvc stack:
  - blueprint to group routes
  - jinja2 view templates
  - file upload save to BLOB db column
  - basic username/password authentication with Werkzeug security
- sqlalchemy orm
- UI css:
  - Sementic-UI is used for page styles
- background job:
  - celery + redis
  - see [`README_celery_redis.md`](./README_celery_redis.md)
- deployment:
  - gunicorn as wsgi server
  - docker container
  - digitalocean k8s cluster deployment

## local run

Setup local runtime environemnt:

```sh
pyenv shell 3.10
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Run flask dev server with debug enabled (which enableds auto-reload).

```sh
FLASK_APP=mvc FLASK_DEBUG=1 python -m flask run

# or run a flash terminal shell:
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

See [`README_celery_redis.md`](./README_celery_redis.md).

## wsgi server with gunicorn

Use gunicorn as wsgi server for deployment.

```sh
gunicorn -b :5000 -w 2 -t 2 --access-logfile - --error-logfile - 'mvc:create_app()' --log-level debug
```

Gthread worker is used when -t is set for multiple threads per worker, where
a threadpool is created in each worker process.
As a result, gthread workers require more memory.

To run the app in a sub-mounted path, use `SCRIPT_NAME` env var to set the
sub-mounted path prefix.

> Sub-mount is needed in kubernetes deployment, where the app is usually deployed
> as a service behind an ingress resource, which is shared with other services,
> by using sub-mount path to distinguish different services.
> See [k8s ingress](./k8s/ingress.yaml)

```sh
SCRIPT_NAME=todo-flask-mvc gunicorn -b :5000 -w 2 -t 2 --access-logfile - --error-logfile - 'mvc:create_app()' --log-level debug

# check the app is running in the sub-mounted path
curl http://localhost:5000/todo-flask-mvc/health
```

## container deployment

For container deployment, use docker to build image and run.

```sh
docker build -t example-todo-flask-mvc .
docker run --name todo-flask-mvc -p 5000:5000 --rm example-todo-flask-mvc
```

## build multi-platform images and push docker hub image registry

In MacOS, run docker buildx to build multi-platform images for x86 amd64 and
arm64. The docker images in docker hub can be deployed to a remote server
such as a kubetnetes cluster.

```sh
# check docker buildx builder instances
docker buildx ls
# if there's only one builder instance, need to create another builder
# instance to support parallel multi-platform builds
docker buildx create --name mybuilder
# use the builder instance
docker buildx use mybuilder

# check dockerhub login status
docker login

# if there are multiple builders active, run multi-platform builds and push in one cli
docker buildx build --platform linux/amd64,linux/arm64,linux/arm64/v8 -t ikalidocker/example-todo-flask-mvc:latest --push .

# OR, run build for a specific platform, such as for local docker desktop
docker buildx build --platform linux/arm64 -t ikalidocker/example-todo-flask-mvc:latest .

# check built image
docker image list
```

Building image and pushing to dockerhub registry within one docker command has
the advantage that docker will automatically add platform metadata to the
built image. This is useful for kubernetes deployment, where the kubernetes
cluster will automatically pull the correct image for the platform it runs on.

To test run a container from dockerhub image:

```sh
docker run --name todo-flask-mvc -p 5000:5000 --env-file .env --rm ikalidocker/example-todo-flask-mvc
```

## kubernetes deployment

See [`k8s/README.md`](./k8s/README.md).


## development notes

To format code, use black and isort.
Isort usually will break black formatting, so run isort first, then run black.

```sh
isort . && black .
```

## project bootstrap

```sh
# create .python-version file with v3.10
pyenv shell 3.10
# venv is natively supported in python v3.4+
python -m venv venv
# activate venv:
source venv/bin/activate
pip install -U pip
# install formatting and import sorting tools
pip install black isort
# install pkgs
pip install flask flask-sqlalchemy python-dotenv toml gunicorn
# update requirements file
pip freeze > requirements.txt
```
