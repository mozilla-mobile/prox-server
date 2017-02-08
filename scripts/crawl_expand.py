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
    statusTable = db.child(venuesTable).child("status").get()

    # Fetch placeIDs to expand 
    location_table = db.child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)
    foundCount = 0

    for placeID in placeIDs:
        placeStatus = statusTable.val()[placeID]
        # Get a list of (src, version) pairs that could be updated, skip searched places
        newSources = [src for src in config if src not in placeStatus or (config[src] > placeStatus[src] and config[src] != 0)]
        if not newSources:
            log.info("No new sources for {}".format(placeID))
            continue
        updatedSources = request_handler.researchPlace(placeID, newSources, placeStatus["identifiers"])
        # Write updated sources to /status
        placeStatus = db.child(venuesTable).child("status").child(placeID)
        for source in newSources:
            placeStatus.update({source: config[source] if source in updatedSources else 0})
        if newSources:
            foundCount += 1
        log.info("{} done: {}".format(placeID, str(updatedSources)))

    log.info("Finished crawling other sources: {} places matched".format(foundCount))


testConfig = { "yelp": 1,
               "tripadvisor": 1 }

chicago_center = (41.8338725,-87.688585)
expandPlaces(testConfig, chicago_center, 30)
