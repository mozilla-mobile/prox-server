import json
import requests
import app.events as events
import app.request_handler as request_handler

KONA_LAT = 19.924301
KONA_LNG = -155.887519
WEEK_DATERANGE = "2016120500-2016120900"
LAT= 50.822327
LNG = -0.13659

SF_LAT = 37.789646
SF_LNG = -122.401051

def fetchEvents():
    eventsList = events.fetchEventsFromLocation(SF_LAT, SF_LNG, 10, 20, "This Week")
    for event in eventsList:
        eventObj = request_handler.getEventfulEventObj(event)
        print(eventObj)
        if eventObj:
            request_handler.writeEventRecord(eventObj)

eventResults = fetchEvents()
