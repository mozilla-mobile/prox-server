import datetime
import re
import requests

import app.search as search
from app.clients import yelpClient, googleapikey, eventfulkey

CALENDAR_URL = 'https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}'
KONA_LAT_LONG = { 'lat': 19.622345, 'lng': -155.665041 }
KONA_RADIUS = 100000

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'

'''
  Best effort to fetch event details (including a Yelp id) from a Google calendar.
  Returns a list of event JSON, each of the form:
    { 'yelp_id':
      'location':
      'event_title':
      'start_time':
      'url':
    }

  All fields are required (locations without a Yelp id will be omitted).
'''

def fetchEventsFromGcal(calId, maxResults, timeRangeMs):
    # Just assume UTC timezone for simplicity
    now = datetime.datetime.utcnow()
    now_rfc = _getRfcTime(now)
    later_rfc = _getRfcTime(now + timeRangeMs)

    eventParams = {'orderBy': 'startTime',
                   'singleEvents': True,
                   'timeMin': now_rfc,
                   'timeMax': later_rfc,
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
    # print(name + '_' + address + '_' + summary)

    # Check address first for lat/long
    if address:
        try:
            addressMapping = search._getAddressIdentifiers(address)
            if addressMapping:
                placeMapping = search._findPlaceInRange(summary, addressMapping['location'], 5)
                if placeMapping:
                    placeName = placeMapping['name']
                    location = placeMapping['location']
                    yelpId = search._guessYelpId(placeName, location['lat'], location['lng'])
                    if yelpId:
                        eventObj = { 'yelp_id': yelpId,
                                     'location': location,
                                     'event_title': summary,
                                     'start_time': event['start']['dateTime'],
                                     'url': event['htmlLink']
                        }
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
                    eventObj = { 'yelp_id': yelpId,
                             'location': location,
                                 'event_title': summary,
                                 'start_time': event['start']['dateTime'],
                                 'url': event['htmlLink']
                    }
                    return eventObj

        except Exception as err:
            print('Searching by name, error: {}'.format(err))

nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def fetchEventsFromLocation(latlong, maxResults, radius):
    params = { 'app_key': eventfulkey,
               'units': 'mi',
               'date': 'Today',
               'sort_order': 'relevance',
               'location': latlong,
               'page_size': maxResults,
               'within': radius }

    r = requests.get(EVENTFUL_URL, params)
    eventList = r.json()['events']['event']
    return eventList

def getEventfulEventObj(event):
    location = { 'lat': event['latitude'], 'lng': event['longitude'] }
    # print(str(event['venue_name']) + '_' + str(event['venue_address']) + '_' + str(event['title']) + '_\n' + str(event['description']) + '\n')
    yelpId = search._guessYelpId(event['venue_name'], location['lat'], location['lng'])
    if yelpId:
        eventObj = { 'yelp_id': yelpId,
                     'location': location,
                     'event_title': event['title'],
                     'start_time': event['start_time'],
                     'url': event['url']
        }
        return eventObj

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()
