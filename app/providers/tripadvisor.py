import re
import requests

from app.clients import tripadvisorkey

idPattern = re.compile("-d([0-9]*)-")

def getNumId(idStr):
    return idPattern.search(idStr).groups(1)[0]

TRIP_ADVISOR_API = "https://api.tripadvisor.com/api/partner/2.0/location/{}"
params = { "key": tripadvisorkey }

def resolve(idObj):
    url = idObj["url"]
    taId = getNumId(url)
    apiUrl = TRIP_ADVISOR_API.format(taId)
    return requests.get(apiUrl, params).json()


TRIP_ADVISOR_LOC_MAPPER_API = 'http://api.tripadvisor.com/api/partner/2.0/location_mapper/{}'
LOC_MAPPER_DEFAULT_PARAMS = { 'key': tripadvisorkey + '-mapper' }


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

    params = dict(LOC_MAPPER_DEFAULT_PARAMS)
    params['q'] = query
    return requests.get(url, params).json()
