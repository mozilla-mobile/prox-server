"""Functions to help find places that are missing data from our providers:
trip advisor, wikipedia, & websites urls.

If you want to read from the production DB, check the repo readme.

TODO:
- Assert schema versions / handle changes. The cache has a version ID we can check against.
- Move this from scripts/.
- Website & Wiki are untested.
"""
from __future__ import print_function

from app import geo
from app.constants import locationsTable, venuesTable
from config import FIREBASE_CONFIG
import app.request_handler as handler
import pyrebase

# We assume every place has yelp.
_KEY_FACTUAL = 'factual'
_KEY_TA = 'tripadvisor'
_KEY_WIKI = 'wikipedia'

_KEY_WEBSITE = 'website'  # In factual child.

_firebase = pyrebase.initialize_app(FIREBASE_CONFIG)


def get_places_missing_provider_data(center, radius_km,
                                     check_missing_ta=True, check_missing_wiki=True, check_missing_web=True):
    """Retrieves a list of place_ids whose places are missing data from at least one of the selected providers.

    :param center: is (lat, lng) as numbers.
    :param radius_km: distance from center we'll check for places missing data.
    :return: a list of place_ids.
    """
    place_caches = _get_place_caches_missing_provider_data(center, radius_km, check_missing_ta, check_missing_wiki, check_missing_web)
    return map(lambda p: p['identifiers']['id'], place_caches)


def _get_place_caches_missing_provider_data(center, radius_km,
                                            check_missing_ta=True, check_missing_wiki=True, check_missing_web=True):
    """Like get_get_places_missing_provider_data but returns the caches directly, for debug purposes."""
    if not (check_missing_ta or check_missing_wiki or check_missing_web): raise ValueError('expected at least one provider')

    required_keys = set()
    if check_missing_ta: required_keys.add(_KEY_TA)
    if check_missing_wiki: required_keys.add(_KEY_WIKI)
    if check_missing_web: required_keys.add(_KEY_FACTUAL)

    location_table = _firebase.database().child(locationsTable).get().val()
    place_ids_in_range = geo.get_place_ids_in_radius(center, radius_km, location_table)
    caches_for_place_ids = handler.readCachedVenueIterableDetails(place_ids_in_range)
    return _filter_caches_by_required_keys(required_keys, caches_for_place_ids)


def _filter_caches_by_required_keys(required_keys, caches_for_place_ids):
    return filter(lambda c: _is_cache_missing_required_keys(required_keys, c), caches_for_place_ids)


def _is_cache_missing_required_keys(required_keys, cache_for_place_id):
    cache_ids = cache_for_place_id.keys()
    for required_id in required_keys:
        if required_id not in cache_ids:
            return True

    # Factual is in required keys so we can get it.
    if _KEY_FACTUAL in required_keys:
        factual_child = cache_for_place_id['factual']
        if _KEY_WEBSITE not in factual_child: return True
    return False
