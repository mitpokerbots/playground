import time
import re
import boto3
import os
import subprocess
import datetime
import zipfile
import jinja2
import random
import json

from backports import tempfile

from server import celery_app, app, db, socketio
from server.models import Bot, Team, Game, GameStatus
from server.helpers import get_s3_object

from sqlalchemy.orm import raiseload

def play_live_game(game):
    time.sleep(4)
    game.status = GameStatus.in_progress
    game.send_message(None)
    time.sleep(4)
    game.status = GameStatus.completed
    game.send_message(None)


@celery_app.task(ignore_result=True)
def play_live_game_task(game_id):
    game = Game.query.get(game_id)
    try:
        play_live_game(game)
    except:
        game.status = GameStatus.internal_error
        game.send_message(None)
