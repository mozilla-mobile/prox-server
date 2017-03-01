from app.constants import searchesTable, venuesTable
from app.firebase import db

print("Purging " + searchesTable)
db().child(searchesTable).remove()

print("Purging " + venuesTable)
db().child(venuesTable).remove()