# -*- coding: utf-8 -*-
import requests
import string
import traceback
import itertools
from multiprocessing.dummy import Pool as ThreadPool
from math import sqrt

from app.clients import yelpClient, factualClient, googleapikey

from app.providers.fs import resolve as resolveFoursquare
from app.providers.yelp import resolve_with_key as resolveYelp
from app.providers.wp import resolve as resolveWikipedia
from app.providers.tripadvisor import resolve_with_key as resolveTripAdvisor
from app.providers.factual_places import resolve as resolveFactualPlace
from app.util import log
from app.constants import venueSearchRadius
import app.geo as geo

from config  import yelpSearchCategories

# The max number of results returned in a single query.
YELP_MAX_PER_PAGE = 40

# 0 = Best matched (default)
# 1 = Distance
# 2 = Highest Rated
YELP_SORT_ORDER = 0

# The max number of results we can obtain by paging. A search may report many
# more results than this, but trying to obtain a result past this number will
# return an error. Note that this number changes depending on the sort order;
# a sort order of 0 returns a maximum of 1000 pageable results, whereas a sort
# order of 1 or 2 returns maximum of just 40.
YELP_MAX_PER_SEARCH = 1000

# An arbitrarily-defined radius that specifies the smallest division we will
# search. If we're still hitting our max search results in this radius, we can
# assume that the places are stacked vertically at a single location, so
# further dividing the area won't help. Note that we shouldn't hit this case
# for a sort order of 0 since we can get up to 1000 places.
YELP_MIN_SEARCH_RADIUS = 50

# For some reason, Yelp searches don't show all matches within a given radius.
# Example: A search at (41.8938244,-87.6428976) with 625m radius doesn't detect
# FLOAT SIXTY (41.893810,-87.636115), less than 400 meters away. Increasing
# the search radius by 40% drastically improves the result set (discovered
# through trial and error).
YELP_RADIUS_FACTOR = 1.4

# CSV list
CATEGORIES = ",".join(yelpSearchCategories)
DEFAULT_COUNTRY_GOOGLEAPI = 'country:US'

resolvers = {
    "foursquare": resolveFoursquare,
    "yelp3": resolveYelp,
    "wikipedia": resolveWikipedia,
    "tripadvisor": resolveTripAdvisor,
    "factual": resolveFactualPlace,
}

def getVenuesFromIndex(lat, lon, radius):
    all = _getVenuesFromIndex(lat, lon, radius, YELP_SORT_ORDER)
    seen = set()
    unique = [biz for biz in all if biz.id not in seen and not seen.add(biz.id) and biz.location.coordinate != None]
    log.info("Found %d unique venues with locations" % len(unique))
    return unique

def _getVenuesFromIndex(lat, lon, radius, sortOrder):
    locality = _singleSearchAPIQuery(lat, lon, radius * YELP_RADIUS_FACTOR, sortOrder, 0)
    log.debug("Crawling point: (%s, %s), radius: %s meters" % (lat, lon, radius))

    # If the current result set is greater than the max we can iterate through,
    # divide the search area and try again. Do this recursively so that we get
    # the full set of places.
    if locality.total > YELP_MAX_PER_SEARCH and radius > YELP_MIN_SEARCH_RADIUS:
        # We're collecting all places inside the square inscribed in the circle
        # defined by the location/radius. Each sub-circle is the smallest
        # circle that contains each quadrant of this square.
        dst = radius / sqrt(8)
        deltaLat = dst / geo.g_METERS_PER_DEGREE_LATITUDE
        deltaLong = geo.metersToLongitudeDegrees(dst, lat)

        def processQuadrant(quad):
            try:
                return _getVenuesFromIndex(lat + quad[0] * deltaLat, lon + quad[1] * deltaLong, radius / 2., sortOrder)
            except Exception as e:
                traceback.print_exc()
                return None

        pool = ThreadPool(4)
        yelpVenues = pool.map(processQuadrant, [(1, 1), (-1, 1), (-1, -1), (1, -1)])
        pool.close()
        pool.join()

        # Abort if any child threw an exception.
        if None in yelpVenues:
            return None

        # Recursively calling _getVenuesFromIndex leaves us with a list of
        # lists, so flatten the result.
        yelpVenues = list(itertools.chain.from_iterable(yelpVenues))

        return yelpVenues

    # Otherwise, iterate through all pages of the result set.
    yelpVenues = locality.businesses
    offset = YELP_MAX_PER_PAGE

    while offset < locality.total:
        locality = _singleSearchAPIQuery(lat, lon, radius * YELP_RADIUS_FACTOR, sortOrder, offset)
        yelpVenues += locality.businesses
        offset += YELP_MAX_PER_PAGE

    return yelpVenues

def _singleSearchAPIQuery(lat, lon, radius, sortOrder, offset):
    opts = {
      "radius_filter": radius,
      "sort": sortOrder,
      "limit": YELP_MAX_PER_PAGE,
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
      # TODO: Handle parsing Crosswalk id out of url in addition to Proxwalk provider id
      info = resolve(idObj)
      if info is not None:
          venueDetails[namespace] = info
    except Exception as err:
        log.exception("Exeption hitting " + namespace)
    return venueDetails

def getVenueDetails(venueIdentifiers, cachedDetails = None):
    if cachedDetails is None:
        cachedDetails = {}
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

