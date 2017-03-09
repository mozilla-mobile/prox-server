"""Geo-related utility functions.

TODO:
- Should this be in a util folder?
- Inefficient to have a firebase instance for every file?

"""
from app.constants import locationsTable
from app.firebase import db

import app.geofire as geofire


def get_place_ids_in_radius(center, radius_km, cached_locations_table=None):
    """Returns all place_ids in the DB within a radius from the given center.
    :param center: is (lat, lng)
    :param cached_locations_table: a direct pull of the geofire `.../location/` table; use this to avoid downloading the table again.
    :return: A set of place ids within the given radius.
    """
    if cached_locations_table is None:
        location_table = _get_locations_table()
    else:
        location_table = cached_locations_table

    place_ids_in_radius = set()
    for place_id, vals in location_table.items():
        if (place_id.startswith("proxdiscover-")):
            continue
        lat, lng = vals['l']
        coord = (lat, lng)
        if geofire.distance(center, coord) <= radius_km:
            place_ids_in_radius.add(place_id)
    return place_ids_in_radius


def _get_locations_table():
    return db().child(locationsTable).get().val()
