"""Utility methods for Google Places."""
from app.clients import gplacesClient

_SEARCH_RADIUS_M = 500  # set arbitrarily


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
