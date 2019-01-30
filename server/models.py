import enum, datetime, uuid, json

from server import app, db, socketio

class Bot(db.Model):
  __tablename__ = 'bots'
  id = db.Column(db.Integer, primary_key=True)
  team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
  team = db.relationship("Team", foreign_keys=team_id, back_populates="bots")
  name = db.Column(db.String(128), nullable=False)
  s3_key = db.Column(db.String(256), nullable=False)

  def __init__(self, team, name, s3_key):
    self.team = team
    self.name = name
    self.s3_key = s3_key


class Team(db.Model):
  __tablename__ = 'teams'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128), unique=True)
  bots = db.relationship("Bot", back_populates="team", primaryjoin=(id == Bot.team_id))

  def __init__(self, name):
    self.name = name


class GameStatus(enum.Enum):
  created = 'created'                # Game has been created, has not been spawned.
  in_progress = 'in_progress'        # Game is currently being played
  internal_error = 'internal_error'  # Game was unable to be played, due to an internal error
  completed = 'completed'            # Game has been completed.


class Game(db.Model):
  __tablename__ = 'games'
  id = db.Column(db.Integer, primary_key=True)
  bot_id = db.Column(db.Integer, db.ForeignKey('bots.id'), nullable=False)
  bot = db.relationship("Bot", foreign_keys=bot_id)
  uuid = db.Column(db.String(128), nullable=False, index=True, unique=True)
  status = db.Column(db.Enum(GameStatus), nullable=False)

  last_message_json = db.Column(db.Text)

  def __init__(self, bot):
    self.bot = bot
    self.status = GameStatus.created
    self.uuid = str(uuid.uuid4())

  @property
  def last_message(self):
    return json.loads(self.last_message_json) if self.last_message_json is not None else None

  def send_message(self, data):
    self.last_message_json = json.dumps(data)
    db.session.commit()
    socketio.emit('game_update', self.as_json(), room=self.uuid)

  def as_json(self):
    return {
      'uuid': self.uuid,
      'bot': {
        'team': self.bot.team.name,
        'name': self.bot.name
      },
      'status': self.status.value,
      'last_message': self.last_message
    }

