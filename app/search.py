from app.clients import yelpClient, factualClient

from app.providers.yelp import resolve as resolveYelp
from app.providers.wp import resolve as resolveWikipedia

CROSSWALK_CACHE_VERSION = 1
# CSV list
CATEGORIES = "beaches" 

resolvers = {
    "yelp": resolveYelp,
    "wikipedia": resolveWikipedia,
}

def _getVenuesFromIndex(lat, lon):
    opts = {
      "radius_filter": 25000,
      "sort": 1,
      "limit": 20, 
      "offset": 0, 
      "category_filter": CATEGORIES
    }
    return yelpClient.search_by_coordinates(lat, lon, **opts)

def _getVenueCrosswalk(yelpID):
    yelpURL = "https://yelp.com/biz/%s" % yelpID
    obj = factualClient.crosswalk().filters({"url": yelpURL}).data()

    mapping = {
      "id": yelpID,
      "version": CROSSWALK_CACHE_VERSION,
      "yelp": {
        "url": yelpURL
      }
    }

    if len(obj) == 0:
        return mapping

    factualID = obj[0]["factual_id"]
    mapping["factualID"] = factualID

    idList = factualClient.crosswalk().filters({"factual_id": factualID}).data()

    for idObj in idList:
        namespace = idObj["namespace"]
        del idObj["factual_id"]
        del idObj["namespace"]
        mapping[namespace] = idObj
    
    return mapping

def _getVenueDetails(venueIdentifiers):
    venueDetails = {}
    for namespace, idObj in venueIdentifiers.iteritems():
        if namespace not in resolvers:
            continue
        resolve = resolvers[namespace]
        info = resolve(idObj)
        if info is None:
            continue
        venueDetails[namespace] = info
    return venueDetails