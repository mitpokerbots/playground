from flask.cli import FlaskGroup
from flask_migrate import Migrate
from server import app, db, socketio
import ssl

cli = FlaskGroup(app)

migrate = Migrate()
migrate.init_app(app, db)

@cli.command("runserver")
def runserver():
    if app.debug:
        socketio.run(app, host='0.0.0.0', port=5001)
    else:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.crt', 'cert.key')
        socketio.run(app, host='0.0.0.0', port=5001, ssl_context=context)

if __name__ == "__main__":
    cli()
