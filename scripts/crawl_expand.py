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
from app.constants import venuesTable, locationsTable, GPS_LOCATIONS
from multiprocessing.dummy import Pool as ThreadPool
from scripts import prox_crosswalk as proxwalk


firebase = pyrebase.initialize_app(FIREBASE_CONFIG)

NOT_FOUND = 0
FETCH_FAILED = -1

def expandPlaces(config, center, radius_km):
    """
    Expands cached venue details by fetching additional sources
    Config is of the form:
        { <provider>: <version> }
    where version is the newest version status
    """
    statusTable = firebase.database().child(venuesTable).child("status").get().val()

    # Fetch placeIDs to expand 
    location_table = firebase.database().child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)

    log.info("{} places found".format(len(placeIDs)))

    def fetchDetails(placeID):
        placeStatus = statusTable[placeID]
        # Get a list of (src, version) pairs that could be updated, skip searched places
        # TODO: Gracefully handle if TripAdvisor-mapper runs out of API calls (25k)
        newProviders = [src for src in config if src not in placeStatus or (config[src] > placeStatus[src] and placeStatus[src] != NOT_FOUND)]
        if not newProviders:
#            log.info("No new sources for {}".format(placeID))
           return

        try:
            placeProviderIDs = proxwalk.getAndCacheProviderIDs(placeID, newProviders, placeStatus["identifiers"])
        except Exception as e:
            log.error("Error fetching or caching provider id: {}".format(e))
            return

        updatedProviders = request_handler.researchPlace(placeID, placeProviderIDs)

        # Write updated sources to /status
        newStatus = makeNewStatusTable(config, updatedProviders, placeProviderIDs, newProviders)

        try:
            placeStatus.update(newStatus)
            firebase.database().child(venuesTable, "status", placeID).update(placeStatus)
        except Exception as e:
            log.error("Error accessing status table for {}: {}".format(placeID, e))

        log.info("{} done: {}".format(placeID, str(updatedProviders)))
    pool = ThreadPool(8)
    pool.map(fetchDetails, placeIDs)

    log.info("Finished crawling other sources")

def makeNewStatusTable(config, updatedProviders, placeProviderIDs, newProviders):
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
    return newStatus

if __name__ == '__main__':
    TEST_CONFIG = { "yelp3": 3,
                    "tripadvisor": 3 }

    expandPlaces(TEST_CONFIG, GPS_LOCATIONS["CHICAGO_CENTER"], 3)
