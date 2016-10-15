import datetime
from pprint import pprint as pp
import re
import requests
import usaddress

from app.clients import yelpClient
from app.clients import googleapikey

CAL_ID = 'hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com'
CALENDAR_URL = 'https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}'
KONA_LAT_LONG = '19.622345,-155.665041'
KONA_RADIUS = 100000

'''
  Best effort to fetch event details (including a Yelp id) from a Google calendar.
  Returns a list of event JSON, each of the form:
    { 'yelp_id':
      'location':
      'event_name':
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

    params = {'orderBy': 'startTime', \
              'singleEvents': True, \
              'timeMin': now_rfc, \
              'timeMax': later_rfc, \
              'maxResults': maxResults }

    r = requests.get(CALENDAR_URL.format(CAL_ID, googleapikey), params)
    items = r.json()['items']
    return items

def getRfcTime(utcTime):
    return utcTime.isoformat('T') + 'Z'

def getLocationInfo(itemLocation, summary):
    name, address = getNameAndAddress(itemLocation)

    # Check address, then name, then summary

    # Check address first for lat/long
    if address:
        print('===address===')
        try:
            ## address => geocode => textsearch.name => Yelp(name, location)
            params = { 'address': address, 'key': googleapikey, 'components': 'country:US' }
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params)
            results = r.json()['results']

            if len(results) > 1:
                result = results[0]
                placeId = result['place_id']
                location = result['geometry']['location']

                params = { 'location': str(location['lat']) + ',' + str(location['lng']), \
                           'radius': 1,
                           'query': summary,
                           'key': googleapikey }

                ## Use textsearch
                r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params)
                results = r.json()['results']

                if len(results) > 0:
                    placeName = results[0]['name']
                    r = yelpClient.search_by_coordinates(location['lat'], location['lng'], \
                                                         limit=1,
                                                         term=placeName)
                    b = r.businesses
                    if len(b) > 0:
                        return (b[0].id, location)

        except Exception as err:
            print('Google Geocaching API: Couldn\'t find item, error: {}'.format(err))

    # Search for location by name
    if name:
        print('==name==')
        params = { 'query': name, \
                   'location': KONA_LAT_LONG, \
                   'radius': 5000, \
                   'key': googleapikey }

        r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params)
        results = r.json()['results']
        if len(results) > 0:
            placeName = results[0]['name']
            location = results[0]['geometry']['location']

            # Find yelp id from name and location
            r = yelpClient.search_by_coordinates(location['lat'], location['lng'], \
                                             limit=1, \
                                             term=placeName)
            b = r.businesses
            if len(b) > 0:
                return (b[0].id, location)

    # Search by summary
    print('==radar==')
    params = { 'keyword': summary, \
               'location': KONA_LAT_LONG, \
               'radius': KONA_RADIUS, \
               'key': googleapikey }

    try:
        r = requests.get('https://maps.googleapis.com/maps/api/place/radarsearch/json', params)
        results = r.json()['results']
        if len(results) > 0:
            result = results[0]
            placeId = result['place_id']
            params = { 'placeid': placeId, \
                       'key': googleapikey }
            res = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params)
            return res.json()['result']['name']

    except Exception as err:
        print('PROBLEM: {}'.format(err))


nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()

eventsList = fetchEvents(CAL_ID, 15, datetime.timedelta(days=7))
for event in eventsList:
    if 'location' in event:
        pp(getLocationInfo(event['location'], event['summary']))
        print('\n')
