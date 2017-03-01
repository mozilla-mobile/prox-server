"""Functions to help find places that are missing data from our providers:
trip advisor, wikipedia, & websites urls.

If you want to read from the production DB, check the repo readme.

TODO:
- Assert schema versions / handle changes. The cache has a version ID we can check against.
- Move this from scripts/.
- Website & Wiki are untested.
"""

from app import geo
from app.constants import locationsTable, venuesTable, GPS_LOCATIONS, Status
from app.firebase import db
import app.request_handler as handler
from pprint import pprint

# We assume every place has yelp.
_KEY_FACTUAL = 'factual'
_KEY_TA = 'tripadvisor'
_KEY_WIKI = 'wikipedia'

_KEY_WEBSITE = 'website'  # In factual child.


def get_places_missing_provider_data(center, radius_km,
                                     check_missing_ta=True, check_missing_wiki=True, check_missing_web=True):
    """Retrieves a list of place_ids whose places are missing data from at least one of the selected providers.

    :param center: is (lat, lng) as numbers.
    :param radius_km: distance from center we'll check for places missing data.
    :return: a list of place_ids.
    """
    place_caches = _get_place_caches_missing_provider_data(center, radius_km, check_missing_ta, check_missing_wiki, check_missing_web)
    return [p['identifiers']['id'] for p in place_caches]


def _get_place_caches_missing_provider_data(center, radius_km,
                                            check_missing_ta=True, check_missing_wiki=True, check_missing_web=True):
    """Like get_get_places_missing_provider_data but returns the caches directly, for debug purposes."""
    if not (check_missing_ta or check_missing_wiki or check_missing_web): raise ValueError('expected at least one provider')

    required_keys = set()
    if check_missing_ta: required_keys.add(_KEY_TA)
    if check_missing_wiki: required_keys.add(_KEY_WIKI)
    if check_missing_web: required_keys.add(_KEY_FACTUAL)

    location_table = db().child(locationsTable).get().val()
    place_ids_in_range = geo.get_place_ids_in_radius(center, radius_km, location_table)
    caches_for_place_ids = handler.readCachedVenueIterableDetails(place_ids_in_range)
    return _filter_caches_by_required_keys(required_keys, caches_for_place_ids)


def _filter_caches_by_required_keys(required_keys, caches_for_place_ids):
    return [c for c in caches_for_place_ids if _is_cache_missing_required_keys(required_keys, c)]


def _is_cache_missing_required_keys(required_keys, cache_for_place_id):
    cache_ids = list(cache_for_place_id.keys())
    for required_id in required_keys:
        if required_id not in cache_ids:
            return True

    # Factual is in required keys so we can get it.
    if _KEY_FACTUAL in required_keys:
        factual_child = cache_for_place_id['factual']
        if _KEY_WEBSITE not in factual_child: return True
    return False

def calculate_crawled_provider_stats(center, radius_km):
    statusTable = db().child(venuesTable, "status").get().val()

    # Fetch placeIDs to check
    location_table = db().child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)

    print("{} total places found".format(len(placeIDs)))

    provider_dict = { "match": {},
                      "no_match": {},
                      "error": {} }

    proxwalkTable = db().child(venuesTable, "proxwalk").get().val()
    prox_dict = {}
    prox_dict["total"] = len(proxwalkTable)

    for placeID in proxwalkTable:
        children = proxwalkTable[placeID]
        for child in children:
            if child not in prox_dict:
                prox_dict[child] = 0
            prox_dict[child] += 1

    provider_dict["proxwalk"] = prox_dict

    for placeID in placeIDs:
        placeStatus = statusTable[placeID]
        for provider in placeStatus:
            if provider == "identifiers":
                continue
            status = placeStatus[provider]
            state = ""
            if status == Status.NOT_FOUND.value:
                state = "no_match"
            elif status == Status.FETCH_FAILED.value:
                state = "error"
            else:
                state = "match"
            state_dict = provider_dict[state]
            newVal = state_dict.get(provider, 0)
            state_dict[provider] = newVal + 1

    pprint(provider_dict)

if __name__ == '__main__':
    radius = 30
    calculate_crawled_provider_stats(GPS_LOCATIONS["CHICAGO_CENTER"], radius)
