from server import app, socketio, db
from flask_script import Manager
from flask_migrate import MigrateCommand

manager = Manager(app)
manager.add_command('db', MigrateCommand)

@manager.command
def runserver():
    socketio.run(app)

if __name__ == '__main__':
    manager.run()
