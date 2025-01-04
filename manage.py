from flask_migrate import MigrateCommand
from flask_script import Manager
from server import app, db, socketio
import ssl

manager = Manager(app)
manager.add_command("db", MigrateCommand)


@manager.command
def runserver():
    if app.debug:
        socketio.run(app, host='0.0.0.0', port=5001)
    else:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.crt', 'cert.key')
        socketio.run(app, host='0.0.0.0', port=5001, ssl_context=context)

if __name__ == "__main__":
    manager.run()
