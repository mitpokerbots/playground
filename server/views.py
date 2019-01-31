from functools import wraps
from flask import abort, session, g, Response, request, render_template
from flask_socketio import emit, join_room
import json

from server import app, db, socketio, redis
from server.models import Game, GameStatus, Bot, Team
from server.tasks import play_live_game_task

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


@socketio.on('request_bots')
def on_request_bots(*args, **kwargs):
  teams = Team.query.all()
  result = { 'teams': [] }
  teams = list(teams)
  teams.sort(key=lambda t: t.name.strip().lower())
  for team in teams:
    new_team = { 'name': team.name, 'bots': [] }
    for bot in team.bots:
      new_team['bots'].append({
        'id': bot.id,
        'name': bot.name
      })
    result['teams'].append(new_team)
  return result


@socketio.on('create_game')
def on_create_game(bot_id):
  bot = Bot.query.get(bot_id)
  game = Game(bot)
  db.session.add(game)
  db.session.commit()
  play_live_game_task.delay(game.id)
  return game.uuid


@socketio.on('join_game')
def on_join_game(game_uuid):
  game = Game.query.filter(Game.uuid == game_uuid).one_or_none()
  if game is None:
    return None

  if game.status == GameStatus.created or game.status == GameStatus.in_progress:
    join_room(game.uuid)
  
  return game.as_json()


@socketio.on('game_ping')
def on_ping(game_uuid):
  redis.publish(game_uuid, 'ping')


@socketio.on('game_action')
def on_action(game_uuid, game_action):
  redis.publish(game_uuid, json.dumps(game_action))
