from datetime import datetime

from celery import Task, shared_task
from sqlalchemy.orm import scoped_session, sessionmaker

from .model import Todo, db

# To call a task periodically you have to add an entry to the beat schedule list.
# This requires beat scheduler worker process to be running, start it with:
# celery -A flask_app.celery_app beat -l info

# beat schedule is configured as celery_app.conf.beat_schedule
# This configuration is imported in create_app() in `mvc/__init__.py` file.
CELERY_BEAT_SCHEDULE = {
    "count-todos-every-5-seconds": {
        "task": "mvc.celery_tasks.count_todos",
        "schedule": 5.0,
        # "args": [{"complete": True}],
        "args": [{"complete": False}],
    },
    # "test-every-3-seconds": {
    #     "task": "mvc.celery_tasks.test",
    #     "schedule": 3.0,  # every 3 seconds
    #     "args": ["hello"],
    #     # enable result storage for this task if needed
    #     "options": {"ignore_result": False},
    # },
}


# To run sqlalchmey session in celery task, a scoped session is needed
# for each task.
# A scoped session represents a registry of Session objects, which is able
# to give each scope (each thread or greenlet) its own Session object.
# In other words, the same thread will get the same Session object every time.
# With scoped session, each celery task will have its own db session, since
# each task function call will fork a new thread to execute the task function.


# With application factory pattern, the db engine is not available in module
# namespace, so a separate db engine is created directly.

from sqlalchemy import create_engine

from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_recycle=3600, pool_size=5)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# This db engine is to be shared with all celery tasks that needs db session.
# The recommended way is to create a abstract base class for celery tasks to
# inherit.

# With scoped session setup above, the celery task will have thread-safe
# db session. However, each celery task forks a new thread that terminates
# when task is completed.
# This task thread is NEVER going to be reused, so the db session associated
# to it has to be closed explicitly to prevent leakage.
# See `session.remove()` in https://docs.sqlalchemy.org/en/20/orm/contextual.html.

# Since the db session is created via scoped session factory in main thread,
# not the forked task thread, it has to be closed in the main thread.

# To acheive this, we use the celery Task class provided `after_return()`
# callback support. This callback function is executed in the main thread
# after the task is returned.
# This function is used to close the db session after the task is returned.

# Since all celery tasks that need db session has this common need. An abstract
# base class is created to implement `session.remove()` in `after_return()` callback.
# See https://docs.sqlalchemy.org/en/20/orm/contextual.html#sqlalchemy.orm.scoped_session.remove.

# All celery tasks that need db session can inherit from this base class for
# db session resource management.


class SqlAlchemyTask(Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""

    abstract = True

    # this is called when task is returned
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()


# @shared_task is preferred over @task because @shared_task decorator is able
# to look for the current celery app, which avoids the explicit import of
# celery_app in module namespace.
# Explicit import of celery_app sometimes causes circular import problem thus
# should be avoided.


@shared_task(base=SqlAlchemyTask, bind=True, ignore_result=False)
def count_todos(self, filters={}) -> int:
    # sqlalchemy session is theread-local, so we need to create a session for
    # each celery task, but it should bind to the same db engine.
    # Session = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
    # session = Session()
    todo_count = db_session.query(Todo).filter_by(**filters).count()
    print(f"todos count (with filters {filters}): {todo_count}")
    # session.close()
    return todo_count


# A task with bind=True will have the task instance (self) passed as the first
# argument to the task function, just like Python bound methods.
# This is useful if you want to access meta-data related to the task execution.


@shared_task(bind=True, ignore_result=False)
def test(self, arg):
    print(f"test task: ({self.request.id}), arg: {arg}, time: {datetime.now()}")
