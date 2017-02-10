# coding=utf-8

import logging
import re
import requests
import sched
import time
import unicodedata

from app.clients import factualClient, tripadvisorkey, yelpClient
from app.constants import statusTable
from config import FIREBASE_CONFIG
import pyrebase
from yelp import errors
from factual import api

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('prox')
log.level = logging.INFO

debugging = log.isEnabledFor(logging.DEBUG)

_slugPattern = re.compile("/([^/\?]*)(\?.*)?$")

def slug(urlString):
    match = _slugPattern.search(urlString)
    return match.group(1)

scheduler = sched.scheduler(time.time, time.sleep)

# Supported APIs for limit checks: "tripadvisor", "factual", "yelp"
def recordAPIStatus(apiName):
    req = True
    try:
        if (apiName == "tripadvisor"):
            ta_test_link = "https://api.tripadvisor.com/api/partner/2.0/location/8364980"
            params = { "key": tripadvisorkey }
            r = requests.get(ta_test_link, params)
            if (r.status_code == 429):
                e_code = r.json().get("code")
                req = False
        elif (apiName == "factual"):
            try:
                cw = factualClient.crosswalk()
                r = cw.filters({"factual_id": "1b5a13e0-d022-4a66-b7cd-9f48801f1196"
}).data()
            except api.APIException as e:
                if e.get_status_code() == 403:
                    # Assume this means API limit has been reached b/c we don't want
                    # to string-check the message (the only place where the specific
                    # error type is listed)
                    req = False
        elif (apiName == "yelp"):
            try:
                # Check an existing location
                yelpClient.get_business("kittea-cat-cafe-san-francisco-4")
            except errors.ExceededReqs:
                req = False
        else:
            raise ValueError("Unknown API name; see app/util.py for API values")
    except Exception as e:
        log.exception("Unknown error while checking for cap limits: %s" % e)

    db = pyrebase.initialize_app(FIREBASE_CONFIG).database()

    # Timestamped response
    response = "{} {} {}".format(req, time.strftime("%a %x %X", time.localtime()), time.tzname[0])

    # Status updated at:
    # https://console.firebase.google.com/project/prox-server-cf63e/database/data/api_availability
    db.child(statusTable).update({apiName: response})
    return req


def strip_url_params(url):
    """Strips params from the url (e.g. "?blah=thing&...") if they exist, else returns the string.
    Assumes the input is a url and results are undefined for non-urls.

    TODO: validate urls so we only strip content from urls. Regex? urllib.parse?
    """
    param_start_index = url.find('?')
    if param_start_index < 0:
        return url
    return url[:param_start_index]


def strip_accents(accented_str):
    """Changes accents into similar looking non-accented letters.
    Characters known to not change: æ œ ø

    via http://stackoverflow.com/a/518232/2219998
    Comments seem to indicate this isn't a perfect solution because of the non-printing representation.
    I did not thoroughly investigate.
    """
    return ''.join(char for char in unicodedata.normalize('NFD', accented_str)
                   if unicodedata.category(char) != 'Mn')


def str_contains_accents(s):
    return s != strip_accents(s)
