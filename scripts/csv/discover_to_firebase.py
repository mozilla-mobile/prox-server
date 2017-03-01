"""Converts the discover form output CSV to firebase data and uploads it.

 Form is available at https://docs.google.com/a/mozilla.com/forms/d/1iBrKNtewo62agBn0Qy21FD2jio6S4247Py4Zhx4-OuQ/edit

 """
from enum import IntEnum
import csv

_ID_PREFIX = 'proxdiscover-'


def getPlaceDataAndWriteToFirebase(path):
    place_data = getPlaceDataFromCSVFile(path)


def getPlaceDataFromCSVFile(path):
    """:return {place-id: {'providers': {'yelp': ...}}, ...}"""
    with open(path) as f:
        reader = csv.reader(f)
        reader.__next__()  # Skip header, which declares fields.
        place_data = [_getPlaceDataFromCSVRow(row) for row in reader]
    return {providers_dict['providers']['yelp']['id']: providers_dict for providers_dict in place_data}


def _getPlaceDataFromCSVRow(row):
    if _isLoadedFromYelpURL(row):
        _placeDataFromYelpURL(row[_FieldIndex.YELP_WHOLE_PLACE_FROM_URL])
    return _csvRowWithCustomDataToPlaceData(row)


def _isLoadedFromYelpURL(row): return row[_FieldIndex.YELP_WHOLE_PLACE_FROM_URL]


def _placeDataFromYelpURL(url):
    """todo:
    - extract id from url
    - get yelp place (yelp.resolve)?
    - get xwalk (researchPlace?)
    - format correctly.
    """


def _csvRowWithCustomDataToPlaceData(row):
    """:return {'providers': {'yelp': ...}}"""
    name = row[_FieldIndex.NAME]
    lat, lng = [float(v) for v in row[_FieldIndex.COORD].split(',')]

    general_place_data = {
        'id': _getIDFromPlaceName(name),
        'name': name,
        'categories': [s.strip() for s in row[_FieldIndex.CATEGORIES].split(',')],
        'website': row[_FieldIndex.WEBSITE],  # todo: how to preserve over yelp url?
        'coordinates': {'lat': lat, 'lng': lng},

        'images': [{'src': url} for url in row[_FieldIndex.PHOTO_URLS].split('\n')],  # todo: validate?
        'hours': _getHoursFromRow(row),
    }

    # We smash all this data in Yelp for ease of access on the client.
    place = {'providers': {'yelp': general_place_data}}

    _appendWikiDataFromRow(row, place)
    _appendYelpDataFromRow(row, place)
    _appendTADataFromRow(row, place)
    return place


def _getIDFromPlaceName(place_name):
    # todo: How does Firebase handle ünicode key names? We'll probably crash if it can't so do nothing until it's a problem.
    formatted_name = place_name.lower().replace(' ', '-')
    return _ID_PREFIX + formatted_name


def _getHoursFromRow(row):
    """:return empty dictionary when no hours, as per client."""
    dayToDayEntry = {
        'monday': row[_FieldIndex.OPEN_HOURS_MON],
        'tuesday': row[_FieldIndex.OPEN_HOURS_TUES],
        'wednesday': row[_FieldIndex.OPEN_HOURS_WED],
        'thursday': row[_FieldIndex.OPEN_HOURS_THURS],
        'friday': row[_FieldIndex.OPEN_HOURS_FRI],
        'saturday': row[_FieldIndex.OPEN_HOURS_SAT],
        'sunday': row[_FieldIndex.OPEN_HOURS_SUN],
    }
    return {day: _parseHoursEntry(dayEntry) for day, dayEntry in dayToDayEntry.items() if dayEntry}


def _parseHoursEntry(entry):
    # Regex validation in form is \d{1,2}:\d{2}-\d{1,2}:\d{2}(,\d{1,2}:\d{2}-\d{1,2}:\d{2})*
    # If we really wanted to be safe, we'd validate the input matches the format ^.
    output_hours = []
    open_periods = entry.split(',')
    for open_period in open_periods:
        open, close = open_period.split('-')
        if len(open) == 4: open = '0' + open
        if len(close) == 4: close = '0' + close
        output_hours.append([open, close])
    return output_hours


def _appendWikiDataFromRow(row, place):
    wiki_provider = {
        'description': row[_FieldIndex.WIKI_DESCRIPTION],
        'url': row[_FieldIndex.WIKI_URL],
    }
    wiki_provider = {k: v for k, v in wiki_provider.items() if v}  # rm empty keys.
    if wiki_provider: place['providers']['wikipedia'] = wiki_provider


def _appendYelpDataFromRow(row, place):
    yelp_provider = {
        'rating': float(row[_FieldIndex.YELP_RATING]),
        'ratingMax': 5,
        'totalReviewCount': int(row[_FieldIndex.YELP_REVIEW_COUNT]),
        'description': row[_FieldIndex.YELP_REVIEW_TEXT],
        'url': row[_FieldIndex.YELP_CLICKED_URL],
    }
    yelp_provider = {k: v for k, v in yelp_provider.items() if v}  # rm empty keys.
    place['providers']['yelp'].update(yelp_provider)


def _appendTADataFromRow(row, place):
    ta_provider = {
        'description': row[_FieldIndex.TA_REVIEW_TEXT],
        'url': row[_FieldIndex.TA_CLICKED_URL],
    }

    rating = row[_FieldIndex.TA_RATING]
    totalReviewCount = row[_FieldIndex.TA_REVIEW_COUNT]
    if rating:
        ta_provider['rating'] = float(rating)
        ta_provider['ratingMax'] = 5
    if totalReviewCount: ta_provider['totalReviewCount'] = int(rating)

    ta_provider = {k: v for k, v in ta_provider.items() if v}  # rm empty keys.
    if ta_provider: place['providers']['tripadvisor'] = ta_provider


class _FieldIndex(IntEnum):
    """Fields that don't get inserted into cards are prefixed by X_"""
    X_TIMESTAMP = 0
    X_INSERT_METHOD = 1
    NAME = 2
    CATEGORIES = 3

    WEBSITE = 4
    COORD = 5
    PHOTO_URLS = 6
    WIKI_DESCRIPTION = 7

    WIKI_URL = 8
    YELP_CLICKED_URL = 9
    YELP_RATING = 10
    YELP_REVIEW_COUNT = 11

    YELP_REVIEW_TEXT = 12
    TA_CLICKED_URL = 13
    TA_RATING = 14
    TA_REVIEW_COUNT = 15

    TA_REVIEW_TEXT = 16
    X_OPEN_HOURS_BRANCH = 17
    OPEN_HOURS_MON = 18
    OPEN_HOURS_TUES = 19

    OPEN_HOURS_WED = 20
    OPEN_HOURS_THURS = 21
    OPEN_HOURS_FRI = 22
    OPEN_HOURS_SAT = 23

    OPEN_HOURS_SUN = 24
    YELP_WHOLE_PLACE_FROM_URL = 25
