# coding=utf-8

import re
import requests

from app import util
from app.clients import tripadvisorkey

idPattern = re.compile("-d([0-9]*)-")

def getNumId(idStr):
    return idPattern.search(idStr).groups(1)[0]

TRIP_ADVISOR_API = "https://api.tripadvisor.com/api/partner/2.0/location/{}"
params = { "key": tripadvisorkey }

def resolve_with_key(key):
    apiUrl = TRIP_ADVISOR_API.format(key)
    res = requests.get(apiUrl, params)
    if res.status_code == 429:
        return None
    else:
        return res.json()

def resolve(idObj):
    """
    Extract id object from Factual Crosswalk id object
    """
    url = idObj["url"]
    taId = getNumId(url)
    return resolve_with_key(taId)

TRIP_ADVISOR_LOC_MAPPER_API = 'http://api.tripadvisor.com/api/partner/2.0/location_mapper/{}'


def _get_loc_mapper_default_params(): return { 'key': tripadvisorkey + '-mapper' }


def search(coord, query):
    """
    Search for a place via TA's location_mapper API:
      https://developer-tripadvisor.com/content-api/documentation/location_mapper/

    This API will return *one* result - TA does the matching on their endpoint. While this is easy, it
    doesn't allow us to make corrections for inaccurate data (e.g. our coord argument is incorrect).

    This API has separated limits from `resolve` and they're increased: 25,000 calls/day and 100 calls/second.

    Note that we could also filter based on categories (hotel, attractions, restaurants)
    but it adds complexity so I opted not to.

    :param coord: a tuple of (lat, long)
    :param query: a string to filter the search by.
    """
    coord_str = ','.join([str(x) for x in coord])
    url = TRIP_ADVISOR_LOC_MAPPER_API.format(coord_str)

    params = _get_loc_mapper_default_params()
    params['q'] = query
    res = requests.get(url, params).json()
    if not _search_query_has_results(res) and util.str_contains_accents(query):
        res = _search_without_accents(query, url)

    # TODO: Further improve results by querying TA without a query_str and doing our own
    # name matching on the results. For example, "Mariposa Baking" (from Yelp) finds no matches
    # despite "Mariposa" being on TA. For a full list of relevant places, see `docs/yelp_ta_name_mismatches.yml`.
    #
    # Implementation notes:
    #   - TA will return at most 10 results
    #   - A place won't necessarily exist in TA (or at that location, e.g. Señor Sisig is a food truck).
    #   - Custom fuzzy matching may introduce more error, making a trade-off between some error & missing data.
    #   - Could also compare address (not just name!)
    return res


def _search_without_accents(query, url):
    """Searches TA location_mapper API, removing the query string's accents.

    Why would you want to? Yelp place names are frequently listed with accents - TA are not, potentially causing
    name mismatches. I've found removing accents corrects some places (e.g. La Mar Cebichería Peruana).
    """
    accent_stripped_str = util.strip_accents(unicode(query))
    params = _get_loc_mapper_default_params()
    params['q'] = accent_stripped_str
    return requests.get(url, params).json()


def _search_query_has_results(res): return len(res['data']) > 0
