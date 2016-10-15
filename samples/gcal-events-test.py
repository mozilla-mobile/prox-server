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

def getLocationInfo(itemLocation):
    name, address = getNameAndAddress(itemLocation)

    # Check address first for lat/long
    if address:
        try:
            params = { 'address': address, 'key': googleapikey, 'components': 'country:US' }
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params)
            pp(r.json())
        except Exception as err:
            print('Google Geocaching API: Couldn\'t find item, error: {}'.format(err))

    # Search for location by name
    elif name:
        try:
            params = { 'input': name, \
                       'location': KONA_LAT_LONG, \
                       'radius': KONA_RADIUS, \
                       'key': googleapikey }

            r = requests.get('https://maps.googleapis.com/maps/api/place/autocomplete/json', params)

            predictions = r.json()['predictions']
            if len(predictions) > 0:
                placeId = predictions[0]['place_id']

                # Get latlong from Places Details
                params = { 'placeid': placeId, \
                           'key': googleapikey }
                r = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params)
                pp(r.json()['result']['geometry']['location'])

        except Exception as err:
            print('Google Autocomplete API: Couldn\'t find item, error: {}'.format(err))

nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()

eventsList = fetchEvents(CAL_ID, 5, datetime.timedelta(days=7))
for event in eventsList:
    if 'location' in event:
        getLocationInfo(event['location'])
