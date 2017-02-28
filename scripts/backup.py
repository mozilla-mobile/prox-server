import json
from app.firebase import db

"""
Backup script for saving contents at the path in Firebase.
"""
def backup(path):
    backup = db().child(path).get().val()
    with open("out.json", "w") as f: json.dump(backup, f)

if __name__ == '__main__':
    # See app/constants for table prefixes and suffixes
    path = "branches/02-chicago/venues"
    backup(path)
