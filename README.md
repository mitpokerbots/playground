# playground
Play against your pokerbot online!

# Instructions to run (similar to scrimmage):
To run locally (cd into directory first), do:

- `brew install rabbitmq scons boost postgres redis` (Optional)
- `initdb --username=postgres ~/pbots; pg_ctl -D ~/pbots -l logfile start; createdb -U postgres pbots`
- `pip install -r requirements.txt`
- Run `redis-server`
- Run `from server import db; db.create_all()` from a python3 shell

To run the server and worker, run in three separate tabs:

- `sudo rabbitmq-server`
- `python manage.py runserver`
- `celery -A server.celery_app worker --loglevel=info --concurrency=1`

Then to run the frontend do:

- `cd client`
- `npm install` (the first time you use it)
- `npm start`

### To import bots into playground
When you originally spin up playground, there are no bots and we need to manually import them.
Bots can be imported by going to the /admin route (like localhost:5001/admin), providing the username and password, and then filling out the text for bots.

In dev environment (local testing), you can enter some dummy value like so: `{"teams": [{"name": local, "bots": [{"name": test_bot, "s3_key": "none"}]}]}`, and you can challenge the reference bot.

In prod (once deployed), you can use the "export to playground" button in scrimmage to make all the current bots visible.
