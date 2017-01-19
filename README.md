# prox-server
This is the server side component to the first NMX prototype project.

# Setup
Set up a virtualenv (assuming you already installed virtualenv with pip) and install dependencies.

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

and `deactivate` to leave the virtualenv.

## Services keys
You need a copy of `./firebase.local.json` and `./keys.local.json`. You can
copy the templates and add your own keys or get the keys from Mozilla's
engineering gdrive. If you don't have access, please contact a team member.

## Firebase
With the keys ready, run:

    python -m samples.firebase-test

You can view real-time changes to the database on the console.

# Testing
Testing is done via [pytest](pytest.org):

    pytest

All tests should pass before landing on `master`.

# Running

The project is a `flask` server which puts jobs on a `rq` task queue.

Thus, the app is run in three parts:

Run redis:

    redis-server

Then run the flask web app:

    python app.py

Then run the workers which will consume the tasks coming from the web server.

    rq worker -c rq_settings

# Pre-caching a location?
Follow the comments in [scripts/crawl_hawaii.py][crawl.py].

[crawl.py]: https://github.com/mozilla-mobile/prox-server/blob/master/scripts/crawl_hawaii.py
