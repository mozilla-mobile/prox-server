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
from scripts import prox_crosswalk as proxwalk

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

NOT_FOUND = 0
FETCH_FAILED = -1

def expandPlaces(config, center, radius_km):
    """
    Expands cached venue details by fetching additional sources
    Config is of the form:
        { <provider>: <version> }
    where version is the newest version status
    """
    statusTable = db.child(venuesTable).child("status").get().val()

    # Fetch placeIDs to expand 
    location_table = db.child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)

    log.info("{} places found".format(len(placeIDs)))
    for placeID in placeIDs:
        placeStatus = statusTable[placeID]
        # Get a list of (src, version) pairs that could be updated, skip searched places
        # TODO: Gracefully handle if TripAdvisor-mapper runs out of API calls (25k)
        newProviders = [src for src in config if src not in placeStatus or (config[src] > placeStatus[src] and placeStatus[src] != NOT_FOUND)]
        if not newProviders:
            log.info("No new sources for {}".format(placeID))
            continue

        try:
            placeProviderIDs = proxwalk.getAndCacheProviderIDs(placeID, newProviders, placeStatus["identifiers"])
        except Exception as e:
            log.error("Error fetching or caching provider id: {}".format(e))
            continue

        updatedProviders = request_handler.researchPlace(placeID, placeProviderIDs)

        # Write updated sources to /status
        newStatus = {}
        for source in config:
            if source in updatedProviders:
                # Fetched provider details
                val = config[source]
            elif source in placeProviderIDs:
                # Couldn't fetch provider details
                val = FETCH_FAILED
            elif source in newProviders:
                # Unable to get provider id
                val = NOT_FOUND
            else:
                continue
            newStatus[source] = val
        try:
            status = db.child(venuesTable, "status", placeID).get().val()
            status.update(newStatus)
            db.child(venuesTable, "status", placeID).update(status)
        except Exception as e:
            log.error("Error accessing status table for {}: {}".format(placeID, e))
            continue

        log.info("{} done: {}".format(placeID, str(updatedProviders)))

    log.info("Finished crawling other sources")


TEST_CONFIG = { "yelp3": 1,
                "tripadvisor": 1,
                "wikipedia": 1 }

CHICAGO_CENTER = (41.8338725, -87.688585)

GARFIELD_PARK = (41.886724, -87.717264)
MUSEUM_SCIENCE_INDUSTRY = (41.790805, -87.583130)
CULTURAL_CENTER = (41.883754, -87.624941)
METROPOLIS_COFFEE = (41.994339, -87.657278)

if __name__ == '__main__':
    expandPlaces(TEST_CONFIG, CHICAGO_CENTER, 30)
