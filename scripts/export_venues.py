from config import FIREBASE_CONFIG
import pyrebase
import app.geo as geo

focus = (19.915403, -155.8961577)

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
for venue in venueData.values():
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

    for p in identifiers.keys():
        factualStats[p] = factualStats.get(p, 0) + 1
    
    print("%.8f, %.8f" % coord)
    providers = venue.get("providers", {}).keys()
    for p in providers:
        stats[p] = stats.get(p, 0) + 1
    if "url" in venue:
        stats["website"] = stats["website"] + 1
    stats["TOTAL"] += 1

print(json.dumps(factualStats, indent=2))
print(json.dumps(stats, indent=2))
