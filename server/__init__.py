import os
from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sslify import SSLify
from flask_socketio import SocketIO

app = Flask(__name__)
config_object_str = 'server.config.ProdConfig' if os.environ.get('PRODUCTION', False) else 'server.config.DevConfig'
app.config.from_object(config_object_str)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
sslify = SSLify(app)
socketio = SocketIO(app, message_queue=app.config['MESSAGE_QUEUE_URL'])

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

import server.views
import server.tasks
