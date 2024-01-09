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

Gunicorn is used as wsgi server for deployment.

Run locally with gunicorn:

```sh
gunicorn -b :5000 -w 2 -t 2 --log-level=debug --access-logfile - --error-logfile - 'mvc:create_app()'
```

- `-b` to bind to a specific ip address and port
- set `-w` to 2 * cpu cores + 1 for deployment
- set `-t` to multiple threads enables thread pool in each worker process
  - by default, Gthread is used by gunicorn, can be changed to gevent with
    `--worker-class gevent`.
  - multi-thread pool is useful for blocking io operations, such as db query,
    http request, etc.
  - multi-threading requires more memory, don't use `-t` for <512MB memory.
- `--log-level` sets the gunicorn logger level
  - gunicorn logger level is different from the flask logger level, thus the 
    flask logger level needs to be set to gunicorn log level, 
    see `mvc.__init__.py` for details
  - gunicorn directs logs below `INFO` level to `stderr`, and `INFO` level and
    above to `stdout`, `stderr` logs are treated as **errors** by cloud container
    monitoring such as datadog, so it's better to set gunicorn log level to
    `INFO` in production depoyment to avoid error alerts
- `--access-logfile -` and `--error-logfile -` redirects access and error logs
  from stderr to stdout, which avoids error alerts in container monitoring.

Gunicorn supports the app in a sub-mounted path, by using `SCRIPT_NAME` env var
to set the sub-mounted path prefix.

The locally run gunicorn served flask app has access to local `.env` file,
which contains a submount path prefix `SCRIPT_NAME`.
For example, if the `SCRIPT_NAME=/todo-flask-mvc`, then the app will be
mounted at `/todo-flask-mvc` url path.

```sh
curl http://localhost:5000/todo-flask-mvc/health
```

For deployment, there's no `.env` file, the keys in `.env` file have to be set
as env vars. For example:

```sh
SCRIPT_NAME=todo-flask-mvc \
LOG_LEVEL=info \
SECRET_KEY=user-a-real-secret-string-for-production \
gunicorn -b :5000 -w 2 -t 2 --log-level=$LOG_LEVEL --access-logfile - --error-logfile - 'mvc:create_app()'
```

In a kubernetes deployment, these env vars can be set in the configmap.
See [k8s config yaml](./k8s/config.yaml)

Additional notes about sub-mount for k8s ingress:

> Sub-mount is needed in kubernetes deployment, where the app is usually deployed
> as a service behind an ingress resource, which is shared with other services,
> by using sub-mount path to distinguish different services.
> See [k8s ingress yaml](./k8s/ingress.yaml)

## build container image and run

Test local docker image build and run, with `test` version suffix:

```sh
docker build -t example-todo-flask-mvc:test .

docker run --name todo-flask-mvc -p 5000:5000 --rm \
  -e "LOG_LEVEL=debug" \
  -e "SCRIPT_NAME=todo-flask-mvc" \
  -e "SECRET_KEY=user-a-real-secret-string-for-production" \
  example-todo-flask-mvc:test
```

## build multi-platform images and push to dockerhub image registry

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

# dockerhub login with access token in shell env var
docker login --username=ikalidocker --password=$DOCKERHUB_TOKEN

echo $DOCKERHUB_TOKEN | docker login --username=ikalidocker --password-stdin

# if there are multiple builders active, run multi-platform builds and push in one cli
docker buildx build --platform linux/amd64,linux/arm64 -t ikalidocker/example-todo-flask-mvc:latest --push .
```

Building image and pushing to dockerhub registry within one docker command has
the advantage that docker will automatically add platform metadata to the
built image. This is useful for kubernetes deployment, where the kubernetes
cluster will automatically pull the correct image for the platform it runs on.

To test run a container from dockerhub image:

```sh
docker pull ikalidocker/example-todo-flask-mvc:latest
docker run --name todo-flask-mvc -p 5000:5000 --rm \
  -e "SCRIPT_NAME=todo-flask-mvc" \
  -e "SECRET_KEY=user-a-real-secret-string-for-production" \
  ikalidocker/example-todo-flask-mvc:latest

# check if the app is running in the sub-mounted path
curl http://localhost:5000/todo-flask-mvc/health
```

## kubernetes deployment

K8s manifests are for digitalocean k8s cluster.

See [`k8s/README.md`](./k8s/README.md).

## other development notes

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
