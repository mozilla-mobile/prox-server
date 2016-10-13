import json
from pprint import pprint as pp

import app.search as search

yelpID = "49-black-sand-beach-kamuela"

venueIdentifiers = search._getVenueCrosswalk(yelpID)

print(json.dumps(venueIdentifiers, indent=2))


venueDetails = search._getVenueDetails(venueIdentifiers)

pp(venueDetails)