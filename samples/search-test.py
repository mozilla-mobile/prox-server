import json
from pprint import pprint as pp

import app.search as search

#yelpID = "49-black-sand-beach-kamuela"
yelpID = "kekaha-kai-state-park-kailua"
#yelpID = "hilton-waikoloa-village-waikoloa-2"
venueIdentifiers = search._getVenueCrosswalk(yelpID)

print(json.dumps(venueIdentifiers, indent=2))


venueDetails = search._getVenueDetails(venueIdentifiers)

pp(venueDetails)