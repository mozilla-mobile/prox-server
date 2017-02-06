"""Crawls existing places in Firebase, expanding their data using multiple
sources.

This script only searches for places that are already in the database; use
`crawl_base.py` to populate the initial set of places.

To cache the results in the production database, see readme.

"""
from app.util import log

import pyrebase
import app.request_handler as request_handler

from config import FIREBASE_CONFIG
from app import geo
from app.constants import venuesTable, locationsTable

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

"""
Expands cached venue details by fetching additional sources
Config is of the form:
    { <provider>: <version> }
where version is the newest version status
"""
def expandPlaces(config, center, radius_km):
    statusCache = db.child(venuesTable).child("status").get()

    # Fetch placeIDs to expand 
    location_table = db.child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)

    for placeID in placeIDs:
        placeStatus = statusCache.val()[placeID]
        # Get a list of (src, version) pairs that could be updated 
        newSources = [src for src in config if src not in placeStatus or config[src] > placeStatus[src]]
        if not newSources:
            continue
        request_handler.researchPlace(placeID, newSources, placeStatus["identifiers"])
        print("done: %s" % placeID)
        exit(0)

testConfig = { "yelp": 1,
               "tripadvisor": 1 }

chicago_center = (41.8338725,-87.688585)
expandPlaces(testConfig, chicago_center, 30)
