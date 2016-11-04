import json
from multiprocessing.dummy import Pool as ThreadPool 

import pyrebase

from config import FIREBASE_CONFIG
from app.constants import venuesTable, eventsTable, searchesTable, searchCacheExpiry, searchCacheRadius
import app.crosswalk as crosswalk
import app.representation as representation
import app.search as search
import app.events as events
from app.util import log

CAL_ID = 'hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com'

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def writeVenueRecord(biz, details, idObj = None):
    key   = representation.createKey(biz)
    try:
        venue = representation.venueRecord(biz, **details)
        geo   = representation.geoRecord(biz)
        record = {
          "details/" + key: venue,
          "locations/" + key: geo 
        }
    except Exception as err:
        log.exception("Exception preparing to write to firebase for key " + key)
        record = {}

    record["cache/" + key] = details
    if idObj is not None:
        # we're now going to cache the details, as well as the crosswalk 
        # identifiers that we used to look them up.
        details["identifiers"] = idObj

    db.child(venuesTable).update(record)

def writeSearchRecord(lat, lng, key=None):
    record = representation._geoRecord(lat, lng)
    from datetime import datetime
    import time
    now = datetime.utcnow()

    record["timestamp"] = now.isoformat()
    record["time"] = time.time()
    db.child(searchesTable).update({ record["g"]: record })

def findSearchRecord(center, radius=1000):
    import app.geo as geo
    import time
    queries = geo.geohashQueries(center, radius)
    now = time.time()

    for query in queries:
        results = db.child(searchesTable).order_by_key().start_at(query[0]).end_at(query[1]).get()
        for result in results.each():
            record = result.val()
            if record.get("time", 0) + searchCacheExpiry < now:
                db.child(searchesTable).child(result.key()).remove()
                continue
            # double check that we're within distance
            circleDistance = geo.distance(center, record["l"]) * 1000
            # 1000 m in 1 km (geo.distance is in km, searchCacheRadius is in m)
            log.info("Circle distance is " + str(circleDistance))
            if circleDistance < searchCacheRadius:
                return record


def readCachedVenueDetails(key):
    try:
        cache = db.child(venuesTable).child("cache/" + key).get().val()
        return cache
    except Exception:
        log.error("Error fetching cached venue details for " + key)

def readCachedVenueIdentifiers(cache):
    if cache is not None:
        return cache.get("identifiers", None)
    return None

def researchVenue(biz):
    try:
        yelpID = representation.createKey(biz)
        cache = readCachedVenueDetails(yelpID)
        venueIdentifiers = readCachedVenueIdentifiers(cache)
        # This gets the identifiers from Factual. It's two HTTP requests 
        # per venue. 
        crosswalkedFoundInCached = venueIdentifiers is None
        if crosswalkedFoundInCached:
            venueIdentifiers, crosswalkAvailable = crosswalk.getVenueIdentifiers(yelpID)

        # This then uses the identifiers to look up (resolve) details.
        # We'll fan out these as much as possible.
        venueDetails = search._getVenueDetails(venueIdentifiers, cache)
    
        # Once we've got the details, we should stash it in 
        # Firebase.
        shouldCacheCrosswalk = (not crosswalkedFoundInCached) or crosswalkAvailable
        if shouldCacheCrosswalk:
            writeVenueRecord(biz, venueDetails, venueIdentifiers)
        else:
            writeVenueRecord(biz, venueDetails)

        return yelpID
    except KeyboardInterrupt:
        return False
    except Exception as err:
        log.exception("Error researching venue")
        return False

def searchLocationWithErrorRecovery(lat, lon):
    try:
        searchLocation(lat, lon)
    except KeyboardInterrupt:
        log.info("GOODBYE")
        sys.exit(1)
    except Exception, err:
        from app.util import log
        log.exception("Unknown exception")

def searchLocation(lat, lon):
    searchRecord = findSearchRecord((lat, lon), searchCacheRadius)
    if searchRecord is not None:
        log.info("searchRecord: %s" % searchRecord)
        return
    else:
        writeSearchRecord(lat, lon)

    locality = search._getVenuesFromIndex(lat, lon)

    yelpVenues = locality.businesses

    pool = ThreadPool(5)

    res = pool.map(researchVenue, yelpVenues)
    pool.close()
    pool.join()

    import json
    log.info("Finished: " + json.dumps(res))

def loadCalendarEvents(numRecords, timeDuration):
    eventsList = events.fetchEventsFromGcal(CAL_ID, numRecords, timeDuration)
    for event in eventsList:
        if 'location' in event:
            eventObj = events.getGcalEventObj(event)
            if eventObj:
                writeEventRecord(eventObj)

def writeEventRecord(eventObj):
    key   = representation.createEventKey(eventObj)
    event = eventObj;

    db.child(eventsTable).update(
      {
        key: event
      }
    )
