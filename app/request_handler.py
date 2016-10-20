from multiprocessing.dummy import Pool as ThreadPool 

import pyrebase

from config import FIREBASE_CONFIG
import app.representation as representation
import app.search as search
from app.util import log

VENUES_KEY = "venues"

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def writeRecord(biz, **details):
    key   = representation.createKey(biz)
    venue = representation.venueRecord(biz, **details)
    geo   = representation.geoRecord(biz)

    db.child(VENUES_KEY).update(
      {
        "details/" + key: venue,
        "locations/" + key: geo 
      }
    )

    return { key: geo }

def researchVenue(biz):
    yelpID = biz.id
    try:
        # This gets the identifiers from Factual. It's two HTTP requests 
        # per venue. 
        venueIdentifiers = search._getVenueCrosswalk(yelpID)
        # This then uses the identifiers to look up (resolve) details.
        # We'll fan out these as much as possible.
        venueDetails = search._getVenueDetails(venueIdentifiers)
        
        # Once we've got the details, we should stash it in 
        # Firebase.
        writeRecord(biz, **venueDetails)
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