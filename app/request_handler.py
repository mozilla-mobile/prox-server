import json
from multiprocessing.dummy import Pool as ThreadPool 

import pyrebase

from config import FIREBASE_CONFIG
from app.constants import venuesTable
import app.crosswalk as crosswalk
import app.representation as representation
import app.search as search
from app.util import log

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def writeVenueRecord(biz, details, idObj = None):
    key   = representation.createKey(biz)
    venue = representation.venueRecord(biz, **details)
    geo   = representation.geoRecord(biz)

    record = {
      "details/" + key: venue,
      "locations/" + key: geo 
    }

    if idObj is not None:
        log.info("caching identifiers for " + key)
        record["identifiers/" + key] = idObj

    db.child(venuesTable).update(record)

    return { key: geo }

def readVenueIdentifiers(key):
    return db.child(venuesTable).child("identifiers/" + key).get().val()

def researchVenue(biz):
    yelpID = biz.id
    try:
        venueIdentifiers = readVenueIdentifiers(yelpID)
        # This gets the identifiers from Factual. It's two HTTP requests 
        # per venue. 
        crosswalkNeeded = venueIdentifiers is None
        if crosswalkNeeded:
            venueIdentifiers, crosswalkAvailable = crosswalk.getVenueIdentifiers(yelpID)

        # This then uses the identifiers to look up (resolve) details.
        # We'll fan out these as much as possible.
        venueDetails = search._getVenueDetails(venueIdentifiers)
        
        # Once we've got the details, we should stash it in 
        # Firebase.
        shouldCacheCrosswalk = (crosswalkNeeded and crosswalkAvailable)
        if shouldCacheCrosswalk:
            writeVenueRecord(biz, venueDetails, venueIdentifiers)
        else:
            writeVenueRecord(biz, venueDetails)

        return yelpID
    except KeyboardInterrupt:
        return False
    except Exception, err: 
        log.exception("Error researching venue")
        return False

def searchLocation(lat, lon):
    locality = search._getVenuesFromIndex(lat, lon)
    yelpVenues = locality.businesses

    pool = ThreadPool(5)

    res = pool.map(researchVenue, yelpVenues)
    pool.close()
    pool.join()

    import json
    log.info("Finished: " + json.dumps(res))