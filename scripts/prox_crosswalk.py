"""A series of helper functions to create a mapping from
yelp IDs to place IDs from other providers in our database.

Intended to be used from a REPL. Primary functions are:
- yelp_ids_to_tripadvisor_ids

TODO:
- Handle hitting API limits
- Handle network errors (e.g. TA API)

"""
from __future__ import print_function
from app.constants import _tablePrefix
from app.providers import tripadvisor as ta
from app.providers import yelp
from config import FIREBASE_CONFIG
import pyrebase

_CROSSWALK_PATH = _tablePrefix + 'crosswalk/'

_firebase = pyrebase.initialize_app(FIREBASE_CONFIG)

CROSSWALK_KEYS = {
    'tripadvisor',
    'website',
    'wikipedia',
}


def _get_crosswalk_db(): return _firebase.database().child(_CROSSWALK_PATH)


def _yelp_id_to_tripadvisor(yelp_id):
    place = yelp.resolve_with_key(yelp_id)
    name = place['name']
    coord = place['coordinates']
    coord_tuple = (coord['latitude'], coord['longitude'])
    return ta.search(coord_tuple, name)


def _yelp_ids_to_raw_tripadvisor(yelp_ids):
    """Takes the given yelp IDs and returns a dictionary of yelp_id to
    a list of matching TA places, as received from the TA API, which is:
    [
      {
        'name': ...,
        'location_id': ...,
        ... # less important stuff
      }
    ]

    Emphasis on the enclosing list. Places with no matches will be an empty list.

    Calling this directly (rather than `yelp_ids_to_tripadvisor_ids`) can be useful for debugging.

    :param yelp_ids: an iterable of yelp IDs
    :return: {<yelp_id>: <data-received-from-TA>, ...}
    """
    out = {}
    for yelp_id in yelp_ids:
        res = _yelp_id_to_tripadvisor(yelp_id)
        ta_place_list = res['data']
        out[yelp_id] = ta_place_list
    return out


def _get_yelp_to_ta_map_from_raw_ta(raw_ta):
    """
    :param raw_ta: output of `yelp_ids_to_raw_tripadvisor`
    :return: {<yelp_id>: <ta_id>}; only the first TA location is used.
    """
    out = {}
    for yelp_id, ta_res in raw_ta.iteritems():
        if len(ta_res) < 1:
            out[yelp_id] = None
        else:
            out[yelp_id] = ta_res[0]['location_id']

            # We take TA's top match so print out if we're dropping any places.
            # We do this because disambiguating would add complexity.
            if len(ta_res) > 1:
                print('More than one match for yelp id, {}, dropping results:'.format(yelp_id))
                for res in ta_res[1:]: print('    {}: {}'.format(res['location_id'], res['name']))
    return out


def yelp_ids_to_tripadvisor_ids(yelp_ids):
    """Primary public TA function.

    :param yelp_ids: an iterable of yelp ids.
    :return: {<yelp_id>: <ta_id>, ...}; if no TA match, <ta_id> is None.
    """
    raw_ta = _yelp_ids_to_raw_tripadvisor(yelp_ids)
    return _get_yelp_to_ta_map_from_raw_ta(raw_ta)