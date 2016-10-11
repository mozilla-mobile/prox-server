from config import FIREBASE_CONFIG
import pyrebase

from pprint import pprint

# This connects to the Firebase endpoint from the FIREBASE_CONFIG and adds some data.
def test_add_values():
    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    pprint(FIREBASE_CONFIG)

    db = firebase.database()
    db_store1 = db.child("store1")

    # Add data (with default timestamped key) 
    timestamped_data = {"key1": "data1"}
    db_store1.push(timestamped_data)

    # Add data with custom key
    key_value_data = {"key2": {"key2_1": "data2"}}
    db_store1.push(key_value_data)

test_add_values()
