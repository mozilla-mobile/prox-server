import datetime
import re
import requests
import sched
import threading
import time

import app.search as search
from app.clients import yelpClient, googleapikey, eventfulkey
from app.constants import calendarInfo, konaLatLng
from app.request_handler import writeEventRecord
from app.request_handler import researchVenue
import app.representation as representation

DAY_DATETIME = datetime.timedelta(days=1)
scheduler = sched.scheduler(time.time, time.sleep)

def startGcalThread():
    scheduler.enter(10, 1, updateFromGcals, ())
    t = threading.Thread(target=scheduler.run)
    t.start()

def updateFromGcals():
    try:
        loadCalendarEvents(DAY_DATETIME)
        scheduler.enter(calendarInfo["calRefreshSec"], 1, updateFromGcals, ())
    except Exception as err:
        from app.util import log
        log.exception("Error running scheduled calendar fetch")
        scheduler.enter(calendarInfo["calRefreshSec"], 1, updateFromGcals, ())

def loadCalendarEvents(timeDuration):
    for calId in calendarInfo["calendarIds"]:
        eventsList = fetchEventsFromGcal(calId, timeDuration)
        for event in eventsList:
            if 'location' in event:
                eventObj = getGcalEventObj(event)
                if eventObj:
                    writeEventRecord(eventObj)

'''
  Best effort to fetch event details (including a Yelp id) from a Google calendar.
  Returns a list of event JSON, each of the form:
    { 'id':
      'coordinates':
      'name':
      'localStartTime':
      'localEndTime':
      'url':
    }

  All fields are required (locations without a Yelp id will be omitted).
'''

def fetchEventsFromGcal(calId, timeRangeMs, startDatetimeUTC=None):
    # Just assume UTC timezone for simplicity
    if not startDatetimeUTC:
        startDatetimeUTC = datetime.datetime.utcnow()
    start_rfc = _getRfcTime(startDatetimeUTC)
    end_rfc = _getRfcTime(startDatetimeUTC + timeRangeMs)

    eventParams = {'orderBy': 'startTime',
                   'singleEvents': True,
                   'timeMin': start_rfc,
                   'timeMax': end_rfc }

    r = requests.get(calendarInfo["googleCalendarUrl"].format(calId, googleapikey), eventParams)
    items = r.json()['items']
    return items

def _getRfcTime(utcTime):
    return utcTime.isoformat('T') + 'Z'

def getGcalEventObj(event):
    # Check address, then name, then summary
    name, address = getNameAndAddress(event['location'])
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
                    yelpBiz = search._guessYelpBiz(placeName, location['lat'], location['lng'])
                    if yelpBiz:
                        researchVenue(yelpBiz)
                        eventObj = representation.eventRecord(yelpBiz.id, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
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
                yelpBiz = search._guessYelpBiz(placeName, location['lat'], location['lng'])
                if (yelpBiz):
                    researchVenue(yelpBiz)
                    eventObj = representation.eventRecord(yelpBiz.id, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
                    return eventObj

        except Exception as err:
            print('Searching by name, error: {}'.format(err))

nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def fetchEventsFromLocation(latlong, maxResults, radius=5, dateRange="Today"):
    params = { 'app_key': eventfulkey,
               'units': 'mi',
               'date': dateRange,
               'sort_order': 'relevance',
               'location': latlong,
               'page_size': maxResults,
               'within': radius }

    r = requests.get(calendarInfo["eventfulUrl"], params)
    eventList = r.json()['events']['event']
    return eventList

def getEventfulEventObj(event):
    locLat = event['latitude']
    locLng = event['longitude']
    yelpBiz = search._guessYelpBiz(event['venue_name'], locLat, locLng)
    if yelpBiz:
        researchVenue(yelpBiz)
        eventObj = representation.eventRecord(yelpBiz.id, locLat, locLng, event['title'], event['start_time'], event['stop_time'], event['url'])
        return eventObj

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()
