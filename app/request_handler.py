from app.util import log
import datetime
from dateutil import parser
import hashlib
import json
from multiprocessing.dummy import Pool as ThreadPool 

from app.constants import \
    venuesTable, venueSearchRadius, venueSearchNumber, \
    eventsTable, cacheTable, \
    searchesTable, searchCacheExpiry, searchCacheRadius, \
    konaLatLng, calendarInfo

from app.clients import yelpClient
from app.firebase import db
import app.crosswalk as crosswalk
import scripts.prox_crosswalk as proxwalk
import app.representation as representation
import app.search as search
import app.events as events
import app.geofire as geo
from app.util import log
import sys

# Writes the set of base records. Note that this performs a single batch update
# operation, so any existing venues will be replaced.
def writeYelpRecords(yelpVenues):
    record = {}

    for biz in yelpVenues:
        key = representation.createKey(biz)
        venue = representation.baseRecord(biz)
        geo = representation.geoRecord(biz)
        status = representation.baseStatus(biz)
        record["details/" + key] = venue
        record["locations/" + key] = geo
        record["status/" + key] = status

    db().child(venuesTable).update(record)

def writeVenueProviderRecord(yelpID, details):
    try:
        venue = representation.updateRecord(yelpID, **details)
        for provider, data in list(venue["providers"].items()):
            db().child(venuesTable, "details", yelpID, "providers").update({provider: data})
    except Exception as e:
        log.error("Error writing record: {}\n{}".format(details, e))

def writeVenueRecord(yelpID, details, idObj = None):
    # idObj is remnant of live-search client calls.
    venue = representation.updateRecord(yelpID, **details)
    db().child(venuesTable, "details", yelpID).update(venue)

def writeSearchRecord(lat, lng, key=None):
    record = representation.geoRecordFromCoord(lat, lng)
    from datetime import datetime
    import time
    now = datetime.utcnow()

    record["timestamp"] = now.isoformat()
    record["time"] = time.time()
    db().child(searchesTable).update({ record["g"]: record })

def readCachedVenueDetails(key):
    try:
        cache = db().child(venuesTable).child("cache/" + key).get().val()
        return cache
    except Exception:
        log.error("Error fetching cached venue details for " + key)

def readCachedVenueIterableDetails(place_ids):
    """Retrieves the cache objects matching the given place IDs.

    This method retrieves the whole cache/ child when making a call so call sparingly.
    We do this because it's slow to make network requests for each child individually.
    To pull down less data, you can use `readCacheVenueDetails`.

    :param place_ids: Iterable of place_ids
    :return: a list of cache objects. If a place_id is not in the cache, it will be dropped from the results.
    """
    out = []
    try:
        cache = db().child(cacheTable).get().val()
        for place_id in place_ids:
            if place_id not in cache: continue
            out.append(cache[place_id])
    except Exception:
        log.error("Error fetching cached venue details for " + place_id)

    return out

def readCachedVenueIdentifiers(cache):
    if cache is not None:
        return cache.get("identifiers", None)
    return None

def researchPlace(keyID, placeProviderIDs):
    try:
        venueDetails = search.getVenueDetails(placeProviderIDs)
        writeVenueProviderRecord(keyID, venueDetails)
        return list(venueDetails.keys())
    except Exception as e:
        log.exception("Error researching venue {}: {}".format(keyID, e))
        return []

def researchVenue(yelpID):
    try:
        cache = readCachedVenueDetails(yelpID)
        venueIdentifiers = readCachedVenueIdentifiers(cache)
        # This gets the identifiers from Factual. It's two HTTP requests 
        # per venue. 
        crosswalkedFoundInCached = venueIdentifiers is None
        if crosswalkedFoundInCached:
            venueIdentifiers, crosswalkAvailable = crosswalk.getVenueIdentifiers(yelpID)

        # This then uses the identifiers to look up (resolve) details.
        # We'll fan out these as much as possible.
        venueDetails = search.getVenueDetails(venueIdentifiers, cache)
    
        # Once we've got the details, we should stash it in 
        # Firebase.
        shouldCacheCrosswalk = (not crosswalkedFoundInCached) or crosswalkAvailable
        if shouldCacheCrosswalk:
            writeVenueRecord(yelpID, venueDetails, venueIdentifiers)
        else:
            writeVenueRecord(yelpID, venueDetails)

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
def searchLocationWithErrorRecovery(lat, lng, radius=None):
    try:
        if radius is None:
            # If the radius is unset, then we should set sensible 
            # defaults
            radius = venueSearchRadius
        searchLocation(lat, lng, radius)
    except KeyboardInterrupt:
        log.exception("GOODBYE")
        sys.exit(1)
    except Exception:
        log.exception("Unknown exception")

def searchLocation(lat, lng, radius):
    yelpVenues = search.getVenuesFromIndex(lat, lng, radius)

    log.debug("Writing venues...")

    writeYelpRecords(yelpVenues)

    log.info("Wrote %d venues" % len(yelpVenues))

def _guessYelpId(placeName, lat, lon):
    safePlaceId = hashlib.md5(placeName).hexdigest()
    cachedId = db().child(eventsTable).child("cache/" + safePlaceId).get().val()
    if cachedId:
        return cachedId

    opts = {
      # 'term': placeName, # Yelp does a bad job with term searching
      'limit': 20,
      #'radius_filter': 1000,
      #'sort_by': 'distance',
      'sort': 1,
    }
    r = yelpClient.search_by_coordinates(lat, lon, **opts)
    if len(r.businesses) > 0:
        location = (lat, lon)
        businessesWithCoords = [b for b in r.businesses if (b.location is not None) and (b.location.coordinate is not None)]
        biz = min(businessesWithCoords, key=lambda b:
            geo.distance(location,
                         (b.location.coordinate.latitude, b.location.coordinate.longitude))
        )
        log.debug("%s --> %s" % (placeName, biz.name))
        researchVenue(biz)

        # Add bizId to cache
        record = { "cache/" +  safePlaceId: str(biz.id) }
        db().child(eventsTable).update(record)

        return biz.id
    else:
        log.info("Can't find %s" % placeName)
        return None

def writeEventRecord(eventObj):
    key   = representation.createEventKey(eventObj)
    event = eventObj;
    geo   = representation.geoRecordFromCoord(float(eventObj["coordinates"]["lat"]), float(eventObj["coordinates"]["lng"]))

    db().child(eventsTable).update(
      {
        "details/" + key: event,
        "locations/" + key: geo
      }
    )

def getEventfulEventObj(event):
    mappingLat, mappingLng = getEventfulMapping(event)
    if (mappingLat != None and mappingLng != None):
        yelpId = _guessYelpId(event['venue_name'], mappingLat, mappingLng)
        # Set local timezone
        startTime, endTime = events.getTimesWithTZ(event["start_time"], event["stop_time"], mappingLat, mappingLng)

        if yelpId:
            eventObj = representation.eventRecord(yelpId, mappingLat, mappingLng, event['title'], str(startTime), str(endTime), event['url'])
            return eventObj

def getEventfulMapping(event):
    venueAddress = event["venue_address"]
    venueName = event["venue_name"]
    mapping = search._getAddressIdentifiers(venueAddress) if venueAddress else search._findPlaceInRange(venueName, event["latitude"], event["longitude"])
    if mapping:
        return (float(mapping["location"]["lat"]), float(mapping["location"]["lng"]))
    else:
        print("no mapping")


def pruneEvents():
    eventDetails = db().child(eventsTable).child("details").get().each()
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
    db().child(eventsTable).update({
        "details/" + key: None,
    #    "cache/" + key: None, # For Kona, do not delete the cache because we hard-code the moz-specific locations
        "locations/" + key: None
    })

def updateFromGcals():
    loadCalendarEvents(datetime.timedelta(weeks=1))

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
