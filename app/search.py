# -*- coding: utf-8 -*-
import requests
import string

from app.clients import yelpClient, factualClient, googleapikey

from app.providers.fs import resolve as resolveFoursquare
from app.providers.yelp import resolve as resolveYelp
from app.providers.wp import resolve as resolveWikipedia
from app.providers.tripadvisor import resolve as resolveTripAdvisor
from app.providers.factual_places import resolve as resolveFactualPlace
from app.util import log
from app.constants import venueSearchRadius

from config  import yelpSearchCategories

CROSSWALK_CACHE_VERSION = 1
# CSV list
CATEGORIES = ",".join(yelpSearchCategories)
DEFAULT_COUNTRY_GOOGLEAPI = 'country:US'

resolvers = {
    "foursquare": resolveFoursquare,
    "yelp": resolveYelp,
    "wikipedia": resolveWikipedia,
    "tripadvisor": resolveTripAdvisor,
    "factual": resolveFactualPlace,
}

def getVenuesFromIndex(lat, lon, radius, maxNum):
    maxNum = min(maxNum, 1000)
    all = _getVenuesFromIndex(lat, lon, radius, "rating", maxNum)
    seen = set()
    unique = (biz for biz in all if biz.id not in seen and not seen.add(biz.id))
    rated = [biz for biz in unique if biz.rating > 3.0]
    return rated

def _getVenuesFromIndex(lat, lon, radius, sortOrder, maxNum):
    total = 1
    offset = 0
    yelpVenues = []
    while offset < total:
        try:
            locality = _singleSearchAPIQuery(lat, lon, offset, radius, sortOrder)
            total = min(locality.total, maxNum)
            yelpVenues += locality.businesses
            offset += 20
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except Exception:
            log.exception("Exception searching with Yelp API")
            # give up if this is the first try – we've seen
            # occasional failures where the location doesn't 
            # have any existing support (e.g. Vanuatu)
            # but also, just randon 500 errors, which we can recover from.
            if total == 1 and offset == 0:
                return yelpVenues
            else:
                offset += 20

    return yelpVenues


def _singleSearchAPIQuery(lat, lon, offset, radius, sortOrder):
    radius = min(radius, 40000)
    opts = {
      "radius_filter": radius,
      "sort_by": sortOrder, 
      "limit": 20, 
      "offset": offset, 
      "category_filter": CATEGORIES
    }
    return yelpClient.search_by_coordinates(lat, lon, **opts)

def _getVenueDetailsFromProvider(args):
     return getVenueDetailsFromProvider(*args)

def getVenueDetailsFromProvider(namespace, idObj, cached):
    venueDetails = {}
    if namespace not in resolvers:
        return venueDetails

    if cached is not None:
        venueDetails[namespace] = cached
        return venueDetails
        
    resolve = resolvers[namespace]
    try:
      info = resolve(idObj)
      if info is not None:
          venueDetails[namespace] = info
    except Exception as err:
        log.exception("Exeption hitting " + namespace)
    return venueDetails

def _getVenueDetails(venueIdentifiers, cachedDetails = None):
    if cachedDetails is None:
        cachedDetails = {}
    from multiprocessing.dummy import Pool as ThreadPool
    args = [(ns, idObj, cachedDetails.get(ns, None)) for ns, idObj in venueIdentifiers.items() if ns in resolvers]
    
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
               'key': googleapikey, }

    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params)
    results = r.json()['results']
    if len(results) > 0:
        r = results[0]
        mapping = {
          "id": r['place_id'],
          "location": r['geometry']['location'],
          "name": r['address_components'][0]['short_name'],
          "zipcode": r['address_components'][-1]['short_name'],
        }
        return mapping
    return None

def _findPlaceInRange(query, lat, lng):
    latlongString = lat + ',' + lng
    params = { 'query': query,
               'key': googleapikey,
               'location': latlongString, }

    results = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params).json()['results']
    if len(results) > 0:
        mapping = {
                'name': results[0]['name'],
                'location': results[0]['geometry']['location']
        }
        return mapping

