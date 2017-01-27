"""A series of helper functions to create a mapping from
yelp IDs to place IDs from other providers in our database.

Intended to be used from a REPL. Primary functions are:
- yelp_ids_to_tripadvisor_ids
  - (for debugging) verify_yelp_id_to_tripadvisor_ids
- write_to_db

TODO:
- Handle hitting API limits
- Handle network errors (e.g. TA API)
- TEST ACCURACY
- Make it easy to run (read place ids from file? store intermediate xw into file? then try atomic update?)
- Make this code re-usable and put into separate files.
- How does this handle incorrect Yelp places?
- Keeps throwing 504: Gateway Time-out from Yelp3Client (rate limit?).

"""
from __future__ import print_function

from app import util
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

# HACK: used to avoid duplicating Yelp place requests.
_YELP_ID_TO_PLACE_CACHE = {}


def _get_crosswalk_db(): return _firebase.database().child(_CROSSWALK_PATH)


def _yelp_id_to_tripadvisor(yelp_id):
    place = _YELP_ID_TO_PLACE_CACHE.get(yelp_id, yelp.resolve_with_key(yelp_id))
    _YELP_ID_TO_PLACE_CACHE[yelp_id] = place
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


def _write_crosswalk_to_db(yelp_id, provider_map):
    """Ensure the given crosswalk object is valid and writes it to the DB.
    Data existing at the given keys will be overwritten.

    :param yelp_id: for the place
    :param provider_map: is {'tripadvisor': <id-str>, ...}
    """
    # Assert 1) no typos, 2) we haven't added keys that this code may not know how to handle.
    for key in provider_map: assert key in CROSSWALK_KEYS
    _get_crosswalk_db().child(yelp_id).update(provider_map)


def write_to_db(yelp_to_ta=None, yelp_to_wiki=None, yelp_to_website=None):
    """Takes yelp_id to other provider ID dicts and writes those values into the crosswalk DB.
    Existing data for a given (yelp_id, other_id) pair will be overwritten.

    :param yelp_to_ta: {<yelp_id>: <ta_id>, ...}; output of `yelp_ids_to_tripadvisor_ids`
    """
    crosswalk = {}  # Bound in fn below.

    def add_ids_to_dict(provider_key, yelp_to_other_id):
        if not yelp_to_other_id: return
        for yelp_id, other_id in yelp_to_other_id.iteritems():
            val = crosswalk.get(yelp_id, {})
            val[provider_key] = other_id
            crosswalk[yelp_id] = val

    add_ids_to_dict('tripadvisor', yelp_to_ta)
    add_ids_to_dict('wikipedia', yelp_to_wiki)
    add_ids_to_dict('website', yelp_to_website)

    for yelp_id, provider_map in crosswalk.iteritems():
        _write_crosswalk_to_db(yelp_id, provider_map)


def verify_yelp_ids_to_tripadvisor_ids(yelp_ids):
    """Returns the expanded output of 1) Yelp -> TA places that match to allow human verification that
    they're the same places and 2) Yelp places that did not match a TA equivalent to allow humans to find
    out why not!

    It is recommended to `pprint` the results.

    :return: {'not_missing_ta': {'yelp': <yelp-place-obj>,
                                 'ta': [<ta-place-obj>, ...]},
              'missing_ta': [<yelp-place-obj>, ...]}
    """
    tas = _yelp_ids_to_raw_tripadvisor(yelp_ids)
    missing_out = []
    not_missing_out = []
    for yelp_id, ta in tas.iteritems():
        yplace = _YELP_ID_TO_PLACE_CACHE.get(yelp_id, yelp.resolve_with_key(yelp_id))  # These should all be cached.
        yout = {'name': yplace['name'],
                'url': util.strip_url_params(yplace['url']),
                'loc': ', '.join(yplace['location']['display_address'])}
        if len(ta) < 1:
            missing_out.append(yout)
            continue

        tout = []
        for ta_place in ta:
            tout.append({'name': ta_place['name'],
                         'id': ta_place['location_id'],
                         'distance': ta_place['distance'],
                         'loc': ta_place['address_obj'].get('address_string', '')})

        val = {'yelp': yout, 'ta': tout}
        not_missing_out.append(val)

    return {'not_missing_ta': not_missing_out,
            'missing_ta': missing_out}
