import datetime
import re
import requests

import app.search as search
from app.clients import googleapikey, eventfulkey
from app.constants import calendarInfo

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

nameAddressRegex = re.compile('^([^0-9]*)([0-9]*.*)')

def fetchEventsFromLocation(lat, lng, maxResults=20, radius=10, dateRange="Today"):
    params = { 'app_key': eventfulkey,
               'units': 'mi',
               'date': dateRange,
               'sort_order': 'relevance',
               'location': str(lat) + "," + str(lng),
               'page_size': maxResults,
               'within': radius }

    r = requests.get(calendarInfo["eventfulUrl"], params)
    if (int(r.json()["total_items"]) > 0):
        eventList = r.json()['events']['event']
        return eventList
    else: return []

def getNameAndAddress(rawLocation):
    output = rawLocation.lower() \
             .strip('()') \
             .split('phone', 1)[0]
    regex = re.search(nameAddressRegex, output) # guess at splitting into (name, address) fields if possible
    return regex.groups()
