from functools import wraps
from flask import abort, session, g, Response, request, render_template
import json

from server import app, db, socketio
from server.models import Game, Bot, Team

def _check_auth(username, password):
  """This function is called to check if a username /
  password combination is valid.
  """
  return username.lower() == 'admin' and password == app.config['ADMIN_PASSWORD']


def _authenticate():
  """Sends a 401 response that enables basic auth"""
  return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'}
  )


def admin_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.authorization
    if not auth or not _check_auth(auth.username, auth.password):
      return _authenticate()
    return f(*args, **kwargs)
  return decorated


def replace_imported_bots(json_text):
    Game.query.delete()
    Bot.query.delete()
    Team.query.delete()
    data = json.loads(json_text)
    for team in data['teams']:
        new_team = Team(team['name'])
        db.session.add(new_team)
        for bot in team['bots']:
            new_bot = Bot(new_team, bot['name'], bot['s3_key'])
            db.session.add(new_bot)
    db.session.commit()


@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_page():
    if request.method == 'POST':
        replace_imported_bots(request.form['export_data'])

    teams = Team.query.all()
    return render_template('admin.html', teams=teams)
