import json
from multiprocessing.dummy import Pool as ThreadPool 

import pyrebase

from config import FIREBASE_CONFIG
from app.constants import venuesTable, eventsTable
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
    venue = representation.venueRecord(biz, **details)
    geo   = representation.geoRecord(biz)

    record = {
      "details/" + key: venue,
      "locations/" + key: geo 
    }

    if idObj is not None:
        cache = details
        cache["identifiers"] = idObj
        record["cache/" + key] = cache

    db.child(venuesTable).update(record)

    return { key: geo }

def readCachedVenueDetails(key):
    cache = db.child(venuesTable).child("cache/" + key).get().val()
    return cache

def readCachedVenueIdentifiers(cache):
    if cache is not None:
        return cache.get("identifiers", None)
    return None

def researchVenue(biz):
    yelpID = biz.id
    try:
        cache = readCachedVenueDetails(yelpID)
        venueIdentifiers = readCachedVenueIdentifiers(cache)
        # This gets the identifiers from Factual. It's two HTTP requests 
        # per venue. 
        crosswalkNeeded = venueIdentifiers is None
        if crosswalkNeeded:
            venueIdentifiers, crosswalkAvailable = crosswalk.getVenueIdentifiers(yelpID)

        # This then uses the identifiers to look up (resolve) details.
        # We'll fan out these as much as possible.
        venueDetails = search._getVenueDetails(venueIdentifiers, cache)
    
        
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
    except Exception as err:
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
