"""This script will read the DB to find places that are missing at least one
datum: trip advisor, wikipedia, & websites. It will output the full `cache/`
data of these places from the DB.

The cache format is:
{
  <provider-name>: <data-direct-from-provider>,
  # repeat for all providers; places missing provider data will be missing the provider key

  'identifiers': <id-data-we-extract-from-provider's-data>
}

It can be run two ways:
 - In a REPL, by calling `get_caches_missing_data`. See method for arg format.
 - By updating the customizable parameter constants and running script: `python -m scripts.places_missing_data`. The caches
   will be printed to stdout.

To get the place ids from the returned caches, run: `place_ids_from_caches`.

If you want to read from the production DB, check the repo readme.

todo: Handle schema updates. The cache has a version ID we can check against.
It'd also be great if we shared all utility fns so they're less likely to go out of date.

"""
from __future__ import print_function

from config import FIREBASE_CONFIG
from app.constants import venuesTable
import app.geo as geo
import pyrebase


# --- START CUSTOMIZABLE PARAMETERS --- #
# The central location we want to search for places around.
FOCUS = (36.162963, -86.780758)  # downtown Nashville

# Distance from focus we'll look for places.
MAX_KM_FROM_FOCUS = 500
# --- END CUSTOMIZABLE PARAMETERS --- #


_LOCATION_TABLE = venuesTable + '/locations'
_CACHE_TABLE = venuesTable + "/cache"

_KEY_FACTUAL = 'factual'
_KEY_TA = 'tripadvisor'
_KEY_WIKI = 'wikipedia'
_REQUIRED_KEYS = {_KEY_FACTUAL, _KEY_TA, _KEY_WIKI}  # Assumes everything has yelp.

_KEY_WEBSITE = 'website'  # In factual child.

_firebase = pyrebase.initialize_app(FIREBASE_CONFIG)


def _get_db():
    """
    `db.child()` & `db.get()` are confusing because they mutate the object's path (add to and completely erase,
    respectively). To keep the path understandable, I use this function to get a new DB ref each time.
    """
    return _firebase.database()


def get_place_ids_in_range(center, max_km, location_table):
    """
    :param center: is (lat, lng)
    """
    out = set()
    for place_id, vals in location_table.iteritems():
        lat, lng = vals['l']
        coord = (lat, lng)
        if geo.distance(center, coord) > max_km:
            continue
        out.add(place_id)
    return out


def _get_cache_for_place_ids(place_ids):
    # It's slow to make network requests for each child individually so we pull down the whole cache child.
    cache = _get_db().child(_CACHE_TABLE).get().val()
    out = []
    for place_id, val in cache.iteritems():
        if place_id not in place_ids: continue
        out.append(val)
    return out


def _is_cache_missing_required_keys(cache_for_place_id):
    cache_ids = cache_for_place_id.keys()
    for required_id in _REQUIRED_KEYS:
        if required_id not in cache_ids:
            return True

    # Factual is in required keys so we can get it.
    factual_child = cache_for_place_id['factual']
    if _KEY_WEBSITE not in factual_child: return True
    return False


def _filter_caches_by_required_keys(caches_for_place_ids):
    return filter(_is_cache_missing_required_keys, caches_for_place_ids)


def get_caches_missing_data(focus=FOCUS, max_km_from_focus=MAX_KM_FROM_FOCUS):
    """
    Primary function in this script.
    :param focus: is (lat, lng) as numbers.
    :param max_km_from_focus: distance from focus we'll check for places missing data.
    :return: the cache format as in the firebase: see file header for format.
    """
    location_table = _get_db().child(_LOCATION_TABLE).get().val()
    place_ids_in_range = get_place_ids_in_range(focus, max_km_from_focus, location_table)
    caches_for_place_ids = _get_cache_for_place_ids(place_ids_in_range)
    return _filter_caches_by_required_keys(caches_for_place_ids)


def place_ids_from_caches(caches):
    return map(lambda v: v['identifiers']['id'], caches)


def main():
    caches_missing_data = get_caches_missing_data()
    print(caches_missing_data)

if __name__ == '__main__': main()
