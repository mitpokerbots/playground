import time
import re
import boto3
import os
import sys
import subprocess
import datetime
import zipfile
import jinja2
import socket
import random
import json

from backports import tempfile

from server import celery_app, app, db, socketio, redis
from server.models import Bot, Team, Game, GameStatus
from server.helpers import get_s3_object
from server.pokerbots_parser.runner import create_runner
from server.bot import Player

from sqlalchemy.orm import raiseload

DEPS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'deps'))
ENGINE_PATH = os.path.join(DEPS_PATH, 'engine', 'engine.py')


# A large portion of this code is copied from mitpokerbots/scrimmage/scrimmage/tasks.py
def render_template(tpl_path, **context):
  tpl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates', tpl_path))
  path, filename = os.path.split(tpl_path)
  return jinja2.Environment(
    loader=jinja2.FileSystemLoader(path or './')
  ).get_template(filename).render(context)


def _verify_zip(zip_file_path):
  try:
    total_size = 0
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
      for info in zip_ref.infolist():
        total_size += info.file_size
    return True, None
  except zipfile.BadZipfile:
    return False, 'Bot zip file is malformed'


def _run_compile_command(command, bot_dir):
  command = subprocess.Popen(
    command,
    cwd=bot_dir,
    env=_get_environment(),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
  )

  output, _ = command.communicate()
  return command.returncode == 0, output


def _compile_bot(bot_dir):
  result = "Cleaning bot dir...\n"

  success, output = _run_compile_command(['scons', '--clean'], bot_dir)
  result += output + "\n"

  if not success:
    return False, result

  result += "Compiling bot...\n"

  success, output = _run_compile_command(['scons'], bot_dir)
  result += output + "\n"

  return success, result

def _download_and_verify(bot, tmp_dir):
  bot_dir = os.path.join(tmp_dir, os.urandom(10).hex())
  os.mkdir(bot_dir)
  bot_download_dir = os.path.join(bot_dir, 'download')
  os.mkdir(bot_download_dir)
  bot_extract_dir = os.path.join(bot_dir, 'source')
  os.mkdir(bot_extract_dir)

  bot_zip_path = os.path.join(bot_download_dir, 'bot.zip')
  with open(bot_zip_path, 'wb') as bot_zip_file:
    if app.debug:
      with open(os.path.join(DEPS_PATH, 'test_bot.zip'), 'rb') as f:
        bot_zip_file.write(f.read())
    else:
      bot_zip_file.write(get_s3_object(bot.s3_key).read())

  valid_zip, msg = _verify_zip(bot_zip_path)
  if not valid_zip:
    return False, msg

  try:
    with zipfile.ZipFile(bot_zip_path, 'r') as z:
      z.extractall(bot_extract_dir)

    bot_dir = None
    for root, dirs, files in os.walk(bot_extract_dir):
      if 'commands.json' in files:
        bot_dir = root
        break

    if bot_dir is None:
      return False, 'Bot dir has no commands.json'

    return True, bot_dir
  except OSError:
    return False, 'Bot zip is missing files. (Maybe missing commands.json?)'


def _get_environment():
  base = os.environ.copy()
  for key in app.config.keys():
    if key in os.environ:
      del base[key]
  return base


def write_config(game_dir, bot_dir):
  with open(os.path.join(game_dir, 'config.py'), 'w') as config_file:
    config_txt = render_template('config.txt', bot_path=bot_dir)
    config_file.write(config_txt)


def run_bot_and_game(game, tmp_dir, bot_dir):
  game_dir = os.path.join(tmp_dir, 'game')
  os.mkdir(game_dir)
  write_config(game_dir, bot_dir)
  engine_process = subprocess.Popen(['python', ENGINE_PATH], cwd=game_dir, env=_get_environment())
  try:
    game.send_message({
      'status': 'starting_game'
    })
    # Give the Java VM some time to start up.
    time.sleep(2)
    pubsub = redis.pubsub()
    pubsub.subscribe(game.uuid)
    player = Player(db_game=game, pubsub=pubsub)
    runner, sock = create_runner(player, 'localhost', 4514)
    print(runner, sock)
    if runner is None or sock is None:
      os.listdir(game_dir)
      os.listdir(bot_dir)
      os.listdir(tmp_dir)
      raise Exception("Couldn't connect to socket")
    player.set_sock(sock)
    runner.run()
  except socket.error:
    pass
  finally:
    engine_process.kill()
    engine_process.wait()

  return "The game is done! Your final bankroll: {}".format(player.bankroll)


def play_live_game(game):
  game.status = GameStatus.in_progress
  game.send_message({
    'status': 'download_and_compile'
  })

  bot = game.bot

  with tempfile.TemporaryDirectory() as tmp_dir:
    success, bot_dir = _download_and_verify(bot, tmp_dir)
    if not success:
      game.status = GameStatus.completed
      game.send_message({
        'message': 'The bot failed to compile, so you win!' + bot_dir
      })
      return

    message = run_bot_and_game(game, tmp_dir, bot_dir)


  game.status = GameStatus.completed
  game.send_message({
    'message': message
  })


@celery_app.task(ignore_result=True)
def play_live_game_task(game_id):
  game = Game.query.get(game_id)
  try:
      play_live_game(game)
  except:
      game.status = GameStatus.internal_error
      game.send_message(None)
      raise
