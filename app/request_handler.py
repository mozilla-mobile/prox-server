from app.util import log
import datetime
from dateutil import parser
import json
from multiprocessing.dummy import Pool as ThreadPool 
import threading

import pyrebase

from config import FIREBASE_CONFIG
from app.constants import \
    venuesTable, venueSearchRadius, venueSearchNumber, \
    eventsTable, \
    searchesTable, searchCacheExpiry, searchCacheRadius, \
    konaLatLng, calendarInfo

from app.clients import yelpClient
import app.crosswalk as crosswalk
import app.representation as representation
import app.search as search
import app.events as events
import app.geo as geo
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

# This is the main entry point for the flask app.
def searchLocationWithErrorRecovery(lat, lng, radius=None, maxNum=None):
    try:
        if radius is None:
            # If the radius is unset, then we should set sensible 
            # defaults
            radius = venueSearchRadius
        if maxNum is None:
            maxNum = venueSearchNumber
        searchLocation(lat, lng, radius, maxNum)
    except KeyboardInterrupt:
        log.exception("GOODBYE")
        sys.exit(1)
    except Exception:
        log.exception("Unknown exception")

def searchLocation(lat, lng, radius, maxNum):
    # Fetch locations
    searchRecord = findSearchRecord((lat, lng), searchCacheRadius)
    if searchRecord is not None:
        log.debug("searchRecord: %s" % searchRecord)
        return
    else:
        writeSearchRecord(lat, lng)

    yelpVenues = search.getVenuesFromIndex(lat, lng, radius, maxNum)
    pool = ThreadPool(5)

    res = pool.map(researchVenue, yelpVenues)

    # Fetch events from Eventful
    eventListings = events.fetchEventsFromLocation(lat, lng)
    eRes = pool.map(researchEvent, eventListings)

    pool.close()
    pool.join()

    import json
    log.info("Found %d: %s" % (len(res), json.dumps(res)))

def _guessYelpId(placeName, lat, lon):
    safePlaceName = placeName.replace(".", "_")
    cachedId = db.child(eventsTable).child("cache/" + safePlaceName).get().val()
    if cachedId:
        return cachedId

    opts = {
      # 'term': placeName,
      'limit': 20,
      'radius_filter': 1000,
      #'radius_filter': 100,
      #'sort_by': 'distance',
      'sort': 1,
    }
    r = yelpClient.search_by_coordinates(lat, lon, **opts)
    if len(r.businesses) > 0:
        location = (lat, lon)
        biz = min(r.businesses, key=lambda b: 
            geo.distance(location, 
                         (b.location.coordinate.latitude, b.location.coordinate.longitude))
        )
        log.debug("%s --> %s" % (placeName, biz.name))
        researchVenue(biz)

        # Add bizId to cache
        record = { "cache/" +  safePlaceName : str(biz.id) }
        db.child(eventsTable).update(record)

        return biz.id
    else:
        log.info("Can't find %s" % placeName)
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
    locLat = float(event['latitude'])
    locLng = float(event['longitude'])

    yelpId = _guessYelpId(event['venue_name'], locLat, locLng)

    # Set local timezone
    startTime, endTime = events.getTimesWithTZ(event["start_time"], event["stop_time"], locLat, locLng)

    if yelpId:
        eventObj = representation.eventRecord(yelpId, locLat, locLng, event['title'], str(startTime), str(endTime), event['url'])
        return eventObj

def pruneEvents():
    eventDetails = db.child(eventsTable).child("details").get().each()
    cutoff = datetime.datetime.today() - datetime.timedelta(days=1, hours=1)

    for event in eventDetails:
        key = event.key()
        if ("localEndTime" not in event.val()):
            deleteEvent(key)
            continue

        endTime = parser.parse(event.val().get("localEndTime"))
        if endTime < cutoff.replace(tzinfo=None):
            deleteEvent(key)

def deleteEvent(key):
    db.child(eventsTable).update({
        "details/" + key: None,
        "cache/" + key: None,
        "locations/" + key: None
    })

def updateFromGcals():
    loadCalendarEvents(datetime.timedelta(days=1))

    # Prune old events
    pruneEvents()

def loadCalendarEvents(timeDuration):
    for calId in calendarInfo["calendarIds"]:
        eventsList = events.fetchEventsFromGcal(calId, timeDuration)
        for event in eventsList:
            if 'location' in event:
                eventObj = getGcalEventObj(event)
                if eventObj:
                    writeEventRecord(eventObj)

def getGcalEventObj(event):
    if ("dateTime" not in event["start"]) or ("dateTime" not in event["end"]) or ("location" not in event):
        return None

    eventLoc = event["location"]
    name, address = events.getNameAndAddress(eventLoc)
    mapping = search._getAddressIdentifiers(eventLoc)
    if mapping:
        try:
            location = mapping['location']
            placeName = '%s, %s' % (mapping['name'], mapping['zipcode'])
            yelpId = _guessYelpId(eventLoc, location['lat'], location['lng'])
            if yelpId:
                optUrl = event["description"] if "description" in event else None
                eventObj = representation.eventRecord(yelpId, location['lat'], location['lng'], event['summary'], event['start']['dateTime'], event['end']['dateTime'], optUrl)
                return eventObj

        except Exception as err:
            log.exception("getGcalEventObj")
    log.info("Unable to find corresponding location for %s" % eventLoc)
