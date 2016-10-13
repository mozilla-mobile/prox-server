import json
import pprint

from app.clients import yelpClient, factualClient
from app.representation import placeRecord

categories="beaches"

def getLocality(lat, lon, **kwargs):
    return yelpClient.search_by_coordinates(lat, lon, **kwargs)

locality = getLocality(19.915403, -155.887403, 
  radius_filter=25000, 
  sort=1, 
  limit=20, 
  offset=0, 
  category_filter=categories
)

businesses = locality.businesses
print(json.dumps([placeRecord(b, {}) for b in businesses], indent=2))
