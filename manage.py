from flask_migrate import MigrateCommand
from flask_script import Manager

from server import app, db, socketio

manager = Manager(app)
manager.add_command("db", MigrateCommand)


@manager.command
def runserver():
    socketio.run(app, host="0.0.0.0")


if __name__ == "__main__":
    manager.run()
