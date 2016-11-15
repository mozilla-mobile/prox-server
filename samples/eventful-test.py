import json
import requests
import app.events as events

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'
KONA_LATLONG = "19.924301, -155.887519"
NUM_RESULTS = 10
WEEK_DATERANGE = "2016120500-2016120900"

def fetchEvents():
    eventsList = events.fetchEventsFromLocation(KONA_LATLONG, NUM_RESULTS, 17, WEEK_DATERANGE)
    return [ events.getEventfulEventObj(event) for event in eventsList ]

eventResults = fetchEvents()
print(json.dumps(eventResults, indent=2))
