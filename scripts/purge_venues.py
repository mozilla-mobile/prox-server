from config import FIREBASE_CONFIG
import pyrebase

# This connects to the Firebase endpoint from the FIREBASE_CONFIG and adds some data.
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)

db = firebase.database()

from app.constants import searchesTable, venuesTable

print("Purging " + searchesTable)
db.child(searchesTable).remove()

print("Purging " + venuesTable)
db.child(venuesTable).remove()