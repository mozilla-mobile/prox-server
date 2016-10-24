import json
import requests

import app.events as events

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'
SF_LATLONG = "37.789225, -122.389521"
NUM_RESULTS = 10

eventsList = events.fetchEventsFromLocation(SF_LATLONG, NUM_RESULTS, 2)
eventObjList = []
for event in eventsList:
    eventObj = events.getEventfulEventObj(event)
    if eventObj:
        eventObjList.append(eventObj)

print(json.dumps(eventObjList, indent=2))
