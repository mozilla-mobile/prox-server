from app.util import log
import datetime
import json
from multiprocessing.dummy import Pool as ThreadPool 
import threading

import pyrebase

from config import FIREBASE_CONFIG
from app.constants import \
    venuesTable, venueSearchRadius, \
    eventsTable, \
    searchesTable, searchCacheExpiry, searchCacheRadius, \
    konaLatLng, calendarInfo

from app.clients import yelpClient
import app.crosswalk as crosswalk
import app.representation as representation
import app.search as search
import app.events as events
from app.util import log, scheduler

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def writeVenueRecord(biz, details, idObj = None):
    key   = representation.createKey(biz)
    key   = key.encode('utf-8').strip()
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
            if circleDistance < searchCacheRadius:
                return record
            log.info("Circle distance is " + str(circleDistance))


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
        yelpID = yelpID.encode('utf-8').strip()
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

def researchEvent(eventfulObj):
    try:
        eventObj = getEventfulEventObj(eventfulObj)
        if eventObj:
            writeEventRecord(eventObj)
            return eventObj["id"]
    except KeyboardInterrupt:
        return False
    except Exception as err:
        log.exception("Error researching venue")
        return False

def searchLocationWithErrorRecovery(lat, lng, radius=None):
    try:
        searchLocation(lat, lng, radius=radius)
    except KeyboardInterrupt:
        log.exception("GOODBYE")
        sys.exit(1)
    except Exception:
        log.exception("Unknown exception")

def searchLocation(lat, lng, radius=None):
    # Fetch locations
    searchRecord = findSearchRecord((lat, lng), searchCacheRadius)
    if searchRecord is not None:
        log.debug("searchRecord: %s" % searchRecord)
        return
    else:
        writeSearchRecord(lat, lng)

    if radius is None: 
        radius = venueSearchRadius

    total = 1
    offset = 0
    yelpVenues = []
    while offset < total:
        locality = search._getVenuesFromIndex(lat, lng, offset=offset, radius=radius)
        total = locality.total
        yelpVenues += locality.businesses
        offset = len(yelpVenues)

    pool = ThreadPool(5)

    res = pool.map(researchVenue, yelpVenues)

    # Fetch events from Eventful
    eventListings = events.fetchEventsFromLocation(lat, lng)
    eRes = pool.map(researchEvent, eventListings)

    pool.close()
    pool.join()

    import json
    log.info("Finished: " + json.dumps(res))

def _guessYelpId(placeName, lat, lon):
    safePlaceName = placeName.replace(".", "_")
    cachedId = db.child(eventsTable).child("cache/" + safePlaceName).get().val()
    if cachedId:
        return cachedId

    opts = {
      'term': placeName[:30],
      'limit': 1
    }
    r = yelpClient.search_by_coordinates(lat, lon, **opts)
    if len(r.businesses) > 0:
        biz = r.businesses[0]
        researchVenue(biz)

        # Add bizId to cache
        record = { "cache/" +  safePlaceName : str(biz.id) }
        db.child(eventsTable).update(record)

        return biz.id
    else:
        return None


def writeEventRecord(eventObj):
    key   = representation.createEventKey(eventObj)
    event = eventObj;
    geo   = representation._geoRecord(float(eventObj["coordinates"]["lat"]), float(eventObj["coordinates"]["lng"]))

    db.child(eventsTable).update(
      {
        "details/" + key: event,
        "locations/" + key: geo
      }
    )

def getEventfulEventObj(event):
    locLat = event['latitude']
    locLng = event['longitude']
    yelpId = _guessYelpId(event['venue_name'], locLat, locLng)
    if yelpId:
        eventObj = representation.eventRecord(yelpId, locLat, locLng, event['title'], event['start_time'], event['stop_time'], event['url'])
        return eventObj

# Fetching events from Google Calendar
def startGcalThread():
    scheduler.enter(10, 1, updateFromGcals, ())
    t = threading.Thread(target=scheduler.run)
    t.setDaemon(True)
    t.start()

def updateFromGcals():
    try:
        loadCalendarEvents(datetime.timedelta(days=1))
        scheduler.enter(calendarInfo["calRefreshSec"], 1, updateFromGcals, ())
    except Exception as err:
        from app.util import log
        log.exception("Error running scheduled calendar fetch")
        scheduler.enter(calendarInfo["calRefreshSec"], 1, updateFromGcals, ())

def loadCalendarEvents(timeDuration):
    for calId in calendarInfo["calendarIds"]:
        eventsList = events.fetchEventsFromGcal(calId, timeDuration)
        for event in eventsList:
            if 'location' in event:
                eventObj = getGcalEventObj(event)
                if eventObj:
                    writeEventRecord(eventObj)

def getGcalEventObj(event):
    # Check address, then name, then summary
    name, address = events.getNameAndAddress(event['location'])
    summary = event['summary']
    if ("dateTime" not in event["start"]) or ("dateTime" not in event["end"]):
        return None

    # Check address first for lat/long
    if address:
        try:
            mapping = search._getAddressIdentifiers(address)
            if mapping:
                placeMapping = search._findPlaceInRange(summary, mapping['location'], 5)
                if placeMapping:
                    location = mapping['location']
                    placeName = placeMapping['name']
                    yelpId = _guessYelpId(placeName, location['lat'], location['lng'])
                    if yelpId:
                        eventObj = representation.eventRecord(yelpId, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
                        return eventObj

        except Exception as err:
            print('Searching by address: error: {}'.format(err))

    # Search for location by name
    if name:
        try:
            mapping = search._findPlaceInRange(name, konaLatLng, 5000)
            if mapping:
                placeName = mapping['name']
                location = mapping['location']
                yelpId = _guessYelpId(placeName, location['lat'], location['lng'])
                if yelpId:
                    eventObj = representation.eventRecord(yelpId, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
                    return eventObj

        except Exception as err:
            print('Searching by name, error: {}'.format(err))
