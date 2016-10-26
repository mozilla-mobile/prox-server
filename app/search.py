import requests

from app.clients import yelpClient, factualClient, googleapikey

from app.providers.yelp import resolve as resolveYelp
from app.providers.wp import resolve as resolveWikipedia
from app.providers.tripadvisor import resolve as resolveTripAdvisor
from app.util import log

CROSSWALK_CACHE_VERSION = 1
# CSV list
CATEGORIES = "beaches" 
DEFAULT_COUNTRY_GOOGLEAPI = 'country:US'

resolvers = {
    "yelp": resolveYelp,
    "wikipedia": resolveWikipedia,
    "tripadvisor": resolveTripAdvisor
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

def _getVenueDetailsFromProvider(arg):
    (namespace, idObj) = arg
    venueDetails = {}
    if namespace not in resolvers:
        return venueDetails

    resolve = resolvers[namespace]
    try:
      info = resolve(idObj)
      if info is not None:
          venueDetails[namespace] = info
    except Exception as err:
        log.exception("Exeption hitting " + namespace)
    return venueDetails

def _getVenueDetails(venueIdentifiers):
    from multiprocessing.dummy import Pool as ThreadPool
    args = [(ns, idObj) for ns, idObj in venueIdentifiers.iteritems() if ns in resolvers]
    
    pool = ThreadPool(10)
    
    results = pool.map(_getVenueDetailsFromProvider, args)

    pool.close()
    pool.join()

    venueDetails = {}
    for d in results:
        venueDetails.update(d)

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

