
import pyrebase

from config import FIREBASE_CONFIG
import app.representation as representation
import app.search as search

VENUES_KEY = "venues"

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

def writeRecord(biz, **details):
    key   = representation.createKey(biz)
    venue = representation.venueRecord(biz, **details)
    geo   = representation.geoRecord(biz)

    db.child(VENUES_KEY).update(
      {
        "details/" + key: venue,
        "locations/" + key: geo 
      }
    )

    return { key: geo }

def searchLocation(lat, lon):
    locality = search._getVenuesFromIndex(lat, lon)
    yelpVenues = locality.businesses
    for biz in yelpVenues:
        yelpID = biz.id
        try:
            venueIdentifiers = search._getVenueCrosswalk(yelpID)
            venueDetails = search._getVenueDetails(venueIdentifiers)
            writeRecord(biz, **venueDetails)
        except: # catch *all* exceptions
            import sys
            e = sys.exc_info()[0]
            print( "Error: %s" % e )