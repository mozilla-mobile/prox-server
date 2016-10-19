import requests
from pprint import pprint as pp

import app.events as events

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'
SF_LATLONG = "37.789225, -122.389521"
NUM_RESULTS = 10

eventsList = events.fetchEventsFromLocation(SF_LATLONG, NUM_RESULTS, 2)
for event in eventsList:
    eventObj = events.getEventfulEventObj(event)
    if eventObj:
        pp(eventObj)
