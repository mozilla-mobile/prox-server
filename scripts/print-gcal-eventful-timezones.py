import datetime
import json

import app.events as events
import app.request_handler as request_handler

SF_LAT, SF_LNG = 37.7749, -122.4194
CAL_ID = "mozilla.com_avh8q3pubnr4uj419aaubpat2g@group.calendar.google.com"

def printEventObj(event):
    eventObj = request_handler.getEventfulEventObj(event)
    if eventObj:
        print(eventObj["utcStartTime"] + " " + eventObj["utcEndTime"])

def fetchEventfulEvents():
    eventListings = events.fetchEventsFromLocation(SF_LAT, SF_LNG, radius=10)
    for listing in eventListings: printEventObj(listing)

def printGcalObj(event):
    eventObj = request_handler.getGcalEventObj(event)
    if eventObj:
        print(eventObj["utcStartTime"] + " " + eventObj["utcEndTime"])

def fetchGcalEvents():
    eventListings = events.fetchEventsFromGcal(CAL_ID, datetime.timedelta(days=1))
    for listing in eventListings: printGcalObj(listing)

print("fetching eventful events")
fetchEventfulEvents()
print("fetching gcal events")
fetchGcalEvents()

