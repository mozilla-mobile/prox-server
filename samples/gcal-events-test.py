import datetime
from pprint import pprint as pp
import re
import requests

from app.clients import yelpClient
from app.clients import googleapikey

CAL_ID = 'hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com'
CALENDAR_URL = 'https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}'
KONA_LAT_LONG = '19.622345,-155.665041'
KONA_RADIUS = 100000
DEFAULT_COUNTRY = 'country:US'

'''
  Best effort to fetch event details (including a Yelp id) from a Google calendar.
  Returns a list of event JSON, each of the form:
    { 'yelp_id':
      'location':
      'event_summary':
      'start_time':
      'url':
    }

  All fields are required (locations without a Yelp id will be omitted).
'''

def fetchEvents(calId, maxResults, timeRangeMs):
    # Just assume UTC timezone for simplicity
    now = datetime.datetime.utcnow()
    now_rfc = getRfcTime(now)
    later_rfc = getRfcTime(now + timeRangeMs)

    eventParams = {'orderBy': 'startTime',
              'singleEvents': True,
              'timeMin': now_rfc,
              'timeMax': later_rfc,
              'maxResults': maxResults }

    r = requests.get(CALENDAR_URL.format(CAL_ID, googleapikey), eventParams)
    items = r.json()['items']
    return items

def getRfcTime(utcTime):
    return utcTime.isoformat('T') + 'Z'

def getEventObj(event):
    # Check address, then name, then summary
    name, address = getNameAndAddress(event['location'])
    summary = event['summary']
    print(name + '_' + address + '_' + summary)

    # Check address first for lat/long
    if address:
        try:
            ## address => geocode => textsearch.name => Yelp(name, location)
            params = { 'address': address,
                       'key': googleapikey,
                       'components': DEFAULT_COUNTRY }

            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params)
            results = r.json()['results']

            if len(results) > 0:
                placeId = results[0]['place_id']
                location = results[0]['geometry']['location']

                params = { 'query': summary,
                           'key': googleapikey,
                           'location': str(location['lat']) + ',' + str(location['lng']),
                           'radius': 5 }

                ## Use textsearch
                r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params)
                results = r.json()['results']

                if len(results) > 0:
                    eventObj = getYelpId(results[0]['name'], location)
                    if (eventObj):
                        return eventObj

        except Exception as err:
            print('Searching by address: error: {}'.format(err))

    # Search for location by name
    if name:
        try:
            params = { 'query': name,
                       'key': googleapikey,
                       'location': KONA_LAT_LONG,
                       'radius': 5000 }

            r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params)
            results = r.json()['results']

            if len(results) > 0:
                placeName = results[0]['name']
                location = results[0]['geometry']['location']

                eventObj = getYelpId(placeName, location)
                if (eventObj):
                    return eventObj

        except Exception as err:
            print('Searching by name, error: {}'.format(err))

    # Search by summary
    params = { 'keyword': summary,
               'location': KONA_LAT_LONG,
               'radius': KONA_RADIUS,
               'key': googleapikey }

    try:
        r = requests.get('https://maps.googleapis.com/maps/api/place/radarsearch/json', params)
        results = r.json()['results']
        #pp(results)
        if len(results) > 0:
            result = results[0]
            placeId = result['place_id']

            params = { 'placeid': placeId,
                       'key': googleapikey }

            result = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params).json()['result']
            placeName = result['name']
            location = result['geometry']['location']

            eventObj = getYelpId(placeName, location)
            if (eventObj):
                return eventObj

    except Exception as err:
        print('Searching by summary, error: {}'.format(err))


nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()

def getYelpId(placeName, locationObj):
    # Find yelp id from name and location
    r = yelpClient.search_by_coordinates(locationObj['lat'], locationObj['lng'], term=placeName[:30], limit=1, radius_limit=5)

    b = r.businesses
    if len(b) > 0:
        return b[0].id

eventsList = fetchEvents(CAL_ID, 5, datetime.timedelta(days=10))
for event in eventsList:
    if 'location' in event:
        pp(getEventObj(event))
        print('\n')
