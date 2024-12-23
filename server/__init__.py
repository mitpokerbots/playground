import os

if os.environ.get('PRODUCTION', False) and os.environ.get('WEB', False):
    from gevent import monkey
    monkey.patch_all()

import urllib.parse as urlparse
from redis import Redis
from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sslify import SSLify
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__, static_folder='build')
CORS(app, resources={r"/*": {"origins": "http://localhost:4000"}})


config_object_str = 'server.config.ProdConfig' if os.environ.get('PRODUCTION', False) else 'server.config.DevConfig'
app.config.from_object(config_object_str)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
sslify = SSLify(app)
socketio = SocketIO(app, message_queue=app.config['MESSAGE_QUEUE_URL'], cors_allowed_origins=["http://localhost:4000"])


def make_redis(flask_app):
    url = flask_app.config['REDIS_URL']
    if url is None:
        raise Exception("Redis not properly configured")
    parsed_url = urlparse.urlparse(url)

    redis = Redis(
        host=parsed_url.hostname or 'localhost',
        port=parsed_url.port or 6379,
        db=int(parsed_url.path[1:] or 0)
    )
    print(redis.ping())
    return redis

def make_celery(flask_app):
    celery = Celery(flask_app.import_name, broker=flask_app.config['CELERY_BROKER_URL'])
    celery.conf.update(flask_app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


celery_app = make_celery(app)
redis = make_redis(app)

import server.views
import server.tasks
