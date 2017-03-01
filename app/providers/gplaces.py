"""Utility methods for Google Places."""
from app.clients import gplacesClient

_SEARCH_RADIUS_M = 500  # set arbitrarily

def resolve_with_key(key):
    gPlace = gplacesClient.get_place(place_id=key)
    if gPlace:
        gPlace.get_details()
        website = gPlace.website
        if website:
            return { "website": website }
        else:
            # Just because a place doesn't have a website does not mean we should error out
            return {}

def search(place_name, coord):
    """Returns the Google place that most closely matches the given place name & coordinates.

    Possible improvements:
    - Verify the returned place matches using fuzzywuzzy
    - Select our favorite match from the returned list of places (e.g. see tripadvisor).

    :param place_name: the place name to match against
    :param coord: is (lat, lng)
    :return: the matching googleplaces.GooglePlacesSearchResult
    """
    lat_lng = {'lat': coord[0], 'lng': coord[1]}
    gplaces = gplacesClient.nearby_search(keyword=place_name, lat_lng=lat_lng, radius=_SEARCH_RADIUS_M)
    if len(gplaces.places) == 0:
        return None
    return gplaces.places[0]
