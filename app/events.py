import datetime
import re
import requests

import app.search as search
from app.clients import yelpClient, googleapikey, eventfulkey
import app.representation as representation

CALENDAR_URL = 'https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}'
KONA_LAT_LONG = { 'lat': 19.622345, 'lng': -155.665041 }
KONA_RADIUS = 100000

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'

'''
  Best effort to fetch event details (including a Yelp id) from a Google calendar.
  Returns a list of event JSON, each of the form:
    { 'id':
      'coordinates':
      'name':
      'startTime':
      'url':
    }

  All fields are required (locations without a Yelp id will be omitted).
'''

def fetchEventsFromGcal(calId, maxResults, timeRangeMs, startDatetimeUTC=None):
    # Just assume UTC timezone for simplicity
    if not startDatetimeUTC:
        startDatetimeUTC = datetime.datetime.utcnow()
    start_rfc = _getRfcTime(startDatetimeUTC)
    end_rfc = _getRfcTime(startDatetimeUTC + timeRangeMs)

    eventParams = {'orderBy': 'startTime',
                   'singleEvents': True,
                   'timeMin': start_rfc,
                   'timeMax': end_rfc,
                   'maxResults': maxResults }

    r = requests.get(CALENDAR_URL.format(calId, googleapikey), eventParams)
    items = r.json()['items']
    return items

def _getRfcTime(utcTime):
    return utcTime.isoformat('T') + 'Z'

def getGcalEventObj(event):
    # Check address, then name, then summary
    name, address = getNameAndAddress(event['location'])
    summary = event['summary']

    # Check address first for lat/long
    if address:
        try:
            mapping = search._getAddressIdentifiers(address)
            if mapping:
                placeMapping = search._findPlaceInRange(summary, mapping['location'], 5)
                if placeMapping:
                    location = mapping['location']
                    placeName = placeMapping['name']
                    yelpId = search._guessYelpId(placeName, location['lat'], location['lng'])
                    if yelpId:
                        eventObj = representation.eventRecord(yelpId, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
                        return eventObj

        except Exception as err:
            print('Searching by address: error: {}'.format(err))

    # Search for location by name
    if name:
        try:
            mapping = search._findPlaceInRange(name, KONA_LAT_LONG, 5000)
            if mapping:
                placeName = mapping['name']
                location = mapping['location']
                yelpId = search._guessYelpId(placeName, location['lat'], location['lng'])
                if (yelpId):
                    eventObj = representation.eventRecord(yelpId, location['lat'], location['lng'], summary, event['start']['dateTime'], event['end']['dateTime'], event['htmlLink'])
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

    r = requests.get(EVENTFUL_URL, params)
    eventList = r.json()['events']['event']
    return eventList

def getEventfulEventObj(event):
    location = { 'lat': event['latitude'], 'lng': event['longitude'] }
    yelpId = search._guessYelpId(event['venue_name'], location['lat'], location['lng'])
    if yelpId:
        eventObj = { 'id': yelpId,
                     'coordinates': location,
                     'description': event['title'],
                     'startTime': event['start_time'],
                     'url': event['url']
        }
        return eventObj

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()
