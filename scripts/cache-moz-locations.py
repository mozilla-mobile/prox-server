'''
Our event location-guessing uses Yelp APIs but they don't do a good job. This script caches and stores the locations that we need.
For Kona, we will not clear out the location or id cache. See 'request_handler.deleteEvent'.
'''

import hashlib
import pyrebase

from app.clients import yelpClient
from app.constants import eventsTable
from app.request_handler import researchVenue
from config import FIREBASE_CONFIG

MOZ_LOCATIONS = {"Hilton Waikoloa Village, 69-425 Waikoloa Beach Dr, Waikoloa Village, HI 96738, USA": "hilton-waikoloa-village-waikoloa-2"}

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def clearEventsDir():
    db.child(eventsTable).remove()

def forceCache(locationDict):
    for key in locationDict:
        yelpID = locationDict[key]
        safePlaceId = hashlib.md5(key).hexdigest()

        # Fetch location and add it to Locations
        biz = yelpClient.get_business(yelpID)
        researchVenue(biz.business)

        record = { "cache/" +  safePlaceId: yelpID }
        db.child(eventsTable).update(record)

forceCache(MOZ_LOCATIONS)
