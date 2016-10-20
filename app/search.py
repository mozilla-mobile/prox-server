import requests

from app.clients import yelpClient, factualClient, googleapikey

from app.providers.yelp import resolve as resolveYelp
from app.providers.wp import resolve as resolveWikipedia
from app.util import log

CROSSWALK_CACHE_VERSION = 1
# CSV list
CATEGORIES = "beaches" 
DEFAULT_COUNTRY_GOOGLEAPI = 'country:US'

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

def _guessYelpId(placeName, lat, lon):
    opts = {
      'term': placeName[:30],
      'limit': 1
    }
    r = yelpClient.search_by_coordinates(lat, lon, **opts)
    if len(r.businesses) > 0:
        return r.businesses[0].id
    else:
        return None

def _getVenueCrosswalk(yelpID):
    yelpURL = "https://yelp.com/biz/%s" % yelpID
    mapping = {
      "id": yelpID,
      "version": CROSSWALK_CACHE_VERSION,
      "yelp": {
        "url": yelpURL
      }
    }
    try:
      obj = factualClient.crosswalk().filters({"url": yelpURL}).data()

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
    except Exception, err:
        log.error("Factual problem with " + yelpID + "; using Yelp only")
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
        try:
            venueDetails[namespace] = info
        except Exception, err:
            log.exception("Exeption hitting " + namespace + " about " + venueIdentifiers["yelp"]["url"])
    return venueDetails

def _getAddressIdentifiers(address):
    params = { 'address': address,
               'key': googleapikey,
               'components': DEFAULT_COUNTRY_GOOGLEAPI }

    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params)
    results = r.json()['results']
    if len(results) > 0:
        mapping = {
          "id": results[0]['place_id'],
          "location": results[0]['geometry']['location']
        }
        return mapping
    return None

def _findPlaceInRange(query, location, radius):
    latlongString = str(location['lat']) + ',' + str(location['lng'])
    params = { 'query': query,
               'key': googleapikey,
               'location': latlongString,
               'radius': radius }

    results = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params).json()['results']
    if len(results) > 0:
        mapping = {
                'name': results[0]['name'],
                'location': results[0]['geometry']['location']
        }
        return mapping

