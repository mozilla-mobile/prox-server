import json
import requests

import app.events as events

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'
KONA_LATLONG = "19.924301, -155.887519"
NUM_RESULTS = 10

eventsList = events.fetchEventsFromLocation(KONA_LATLONG, NUM_RESULTS, 17, "2016120500-2016120900")
eventObjList = []
for event in eventsList:
    eventObj = events.getEventfulEventObj(event)
    if eventObj:
        eventObjList.append(eventObj)

print(json.dumps(eventObjList, indent=2))
