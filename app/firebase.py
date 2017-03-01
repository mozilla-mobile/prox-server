from config import FIREBASE_CONFIG
import pyrebase

_pyrebase = pyrebase.initialize_app(FIREBASE_CONFIG)


def db():
    """Returns a new database reference via pyrebase."""
    return _pyrebase.database()