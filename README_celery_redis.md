To support background jobs, Celery requires a message broker to send and receive
messages. Redis is selected as the message broker.

Install packages:

```sh
pip install celery redis
```

Celery object `celery_app` is created in the `create_app()`, which imports the
init function from `celery_init.py`.
The celery app object is exposed in `celery_app.py`. It is used to invoke celery
procresses such as worker and scheduler.

```sh
celery --app mvc.celery_app worker --loglevel=info
```

Celery tasks are defined in `celery_tasks.py`.

In a separate terminal, start main flask app shell to test a celery task:

```sh
FLASK_DEBUG=True FLASK_APP=mvc flask shell
```

In the flask shell, import the celery task function and call it with delay():

```python
from mvc.celery_tasks import test
# calling the delay() method on the celery task function will return an
# AsyncResult object
async_result = test.delay("hello celery")
# a UUID task id is assigned to the AsyncResult object id attribute
async_result.id
'b0e018ca-7955-44d9-8046-f60f3241d2d7'

# In any flask runtime thread, we can hydrate this async_result object by id.
# Because this task function is configured ignore_result=False, its status
# and result will be stored in the backend redis and available to fetch.
from celery.result import AsyncResult
ar = AsyncResult('b0e018ca-7955-44d9-8046-f60f3241d2d7')
# The ready() method returns whether the task has finished processing or not>>>> ar.ready()
True
# A task can only be in a single state, but it can progress through several
# states. The stages transfer can be:
# PENDING -> STARTED -> SUCCESS | FAILURE | RETRY -> STARTED -> SUCCESS ...
ar.status
'SUCCESS'
ar.successful()
True
ar.failed()
False
# for a failed task, .get() will raise an exception
ar.get()
```

The worker terminal should show that the task is received and executed:

```sh
[2023-10-01 16:50:09,001: WARNING/ForkPoolWorker-8] test task: (2dfe014e-322a-40a9-b75f-e432d9ac6553), arg: hello celery, time: 2023-10-01 16:50:09.000781
[2023-10-01 16:50:09,002: INFO/ForkPoolWorker-8] Task mvc.celery_tasks.test[2dfe014e-322a-40a9-b75f-e432d9ac6553] succeeded in 0.0019694170041475445s: None
```

NOTE:
Backends use resources to store and transmit results. To ensure that resources
are released, you must eventually call get() or forget() on EVERY AsyncResult
instance returned after calling a task.

To call a group of tasks:

- use celery group object
- use task function's .s() (short for signature()) method to create a signature object
- collect a list of AsyncResult objects as group result (type celery.result.GroupResult)

```python
from celery import group
from mvc.celery_tasks import test

group_result = group(test.s(f"hello {i}") for i in range(10))()

[r.status for r in group_result]
['SUCCESS', 'SUCCESS', 'SUCCESS', ...]
group_result[1].get()
```

For periodic tasks, use celery beat scheduler.
Periodic tasks are configured in `beat_schedule` dict.

To run period tasks:

- celery worker process must be started to wait for the enqued tasks
- celery beat scheduler process must be started to schedule the periodic tasks

Start a worker process as shown above,
and then start a beat scheduler process in a separate terminal:

```sh
celery -A  mvc.celery_app beat --loglevel=info
```

Other useful celery commands:

```sh
# check celery status
celery -A  mvc.celery_app status
# check currently active workers:
celery -A mvc.celery_app inspect active

# enable events to monitor celery events
celery -A mvc.celery_app control enable_events
# use event --dump as tail -f to monitor celery events
celery -A mvc.celery_app events --dump
# always disable events when done monitoring
celery -A mvc.celery_app disable_events
```

Ref: general usage of celery:
https://docs.celeryq.dev/en/stable/userguide/index.html#guide

## Redis setup for Celery

Redis serves as both the message broker and the result backend for Celery.

### redis setup in local docker

```sh
docker pull redis
# redis needs a bridge network to connect to
docker network create -d bridge redisnet
# check network
docker network ls | grep redisnet
# run redis container with bridge network
docker run -d -p 6379:6379 --name docker-redis --network redisnet redis
# check redis container with its built-in redis-cli tool
docker exec -it docker-redis redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> dbsize
(integer) 0
# list all existing keys
127.0.0.1:6379> keys *
(empty array)
# remove all keys
127.0.0.1:6379> flushall
OK
127.0.0.1:6379> exit
```

### redis setup in gcp

```sh
gcloud config set project poc-data-platform-289915
gcloud redis instances list --region=us-east4
# create a redis instance with 1GB memory size
gcloud redis instances create redis-instance --size=1 --region=us-east4
# check created redis instance
gcloud redis instances describe redis-instance --region=us-east4

# to test connection to the redis instance, create a VM instance in the same VPC
kubectl run tmp-shell --rm -i --tty --restart=Never --image ubuntu -- bin/bash

# in the vm bash, as root, install redis-cli
root@tmp-shell:/# apt-get update && apt-get install telnet redis-tools

# connect to redis instance using telnet
root@tmp-shell:/# telnet 10.74.20.27 6379

# invoke redis shell
root@tmp-shell:/# redis-cli -h 10.74.20.27
# in redis shell
10.74.20.27:6379> PING
PONG
10.74.20.27:6379> DBSIZE
(integer) 0
10.74.20.27:6379> exit
root@tmp-shell:/#

# when done, exit the vm shell and it will be deleted automatically
root@tmp-shell:/# exit
exit
pod "tmp-shell" deleted
```
