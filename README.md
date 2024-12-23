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
