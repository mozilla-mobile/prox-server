# prox-server
This is the server side component to the first NMX prototype project.

# Setup
Set up a virtualenv (assuming you already installed virtualenv with pip) and install dependencies.

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

and `deactivate` to leave the virtualenv.

## Firebase
Add the path to the Firebase credentials json file to `config.py`, and then run

    python firebase-test.py

You can view real-time changes to the database on the console.
