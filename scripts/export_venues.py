"""Logs debug information about a specific location from Firebase.

For sample output (1/18/17) and a brief explanation, see:
https://gist.github.com/mcomella/15b5a9fc9140e9d6c9070e0380d700b9

To visualize the returned GPS coordinates, hampster map is recommended.

To log results from the production database, see readme.

"""
from config import FIREBASE_CONFIG
import pyrebase
import app.geofire as geo

# --- START MODIFIABLE PARAMETERS --- #
# The location around which you'd like to log.
focus = (19.915403, -155.8961577)
# --- END MODIFIABLE PARAMETERS --- #

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

from app.constants import venuesTable

venueTableComplete = db.child(venuesTable).get().val()
venueData = venueTableComplete["details"]
cacheData = venueTableComplete["cache"]

import json
stats = {
  "website"    : 0,
  "TOTAL"      : 0,
}
factualStats = {}
for venue in list(venueData.values()):
    yelpID = venue["id"]
    coord = venue["coordinates"]
    coord = (coord["lat"], coord["lng"])

    if geo.distance(coord, focus) > 500: # 500 km
        continue

    identifiers = None
    try:
        identifiers = cacheData[yelpID]["identifiers"]
    except KeyError:
        identifiers = dict()

    for p in list(identifiers.keys()):
        factualStats[p] = factualStats.get(p, 0) + 1
    
    print("%.8f, %.8f" % coord)
    providers = list(venue.get("providers", {}).keys())
    for p in providers:
        stats[p] = stats.get(p, 0) + 1
    if "url" in venue:
        stats["website"] = stats["website"] + 1
    stats["TOTAL"] += 1

print(json.dumps(factualStats, indent=2))
print(json.dumps(stats, indent=2))
