import datetime
import hashlib
import random

from app.util import log
from collections import OrderedDict
from dateutil import parser
from .events import isSingleDayEvent

def baseRecord(biz):
    # biz is the response object from the Yelp Search API

    coord = {
      "lat": biz.location.coordinate.latitude,
      "lng": biz.location.coordinate.longitude
    }

    return {
      "providers": {
        "yelp": {
          "id"              : biz.id,
          "address"         : biz.location.display_address,
          "coordinates"     : coord,
          "description"     : biz.snippet_text,
          "name"            : biz.name,
          "phone"           : biz.display_phone,
          "rating"          : biz.rating,
          "ratingMax"       : 5,
          "totalReviewCount": biz.review_count,
          "url"             : biz.url,
        }
      }
    }

def updateRecord(yelpID, **details):
    providers = {}

    # Yelp v3.
    if "yelp3" in details:
      info = details["yelp3"]
      categories = None
      if "categories" in info:
        categories = [
          c["alias"] for c in info["categories"]
          if "alias" in c
        ]
      providers["yelp3"] = {
        "images"    : _imageRecords(info.get("photos", []), info["url"]),
        "hours"     : _yelpHoursRecord(info.get("hours", None)),
        "categories": categories,
      }

    # Wikipedia.
    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url"        : info["url"],
        "description": info["summary"],
        "images"     : _imageRecords(info["images"], info["url"])
      }

    # TripAdvisor
    if "tripadvisor" in details:
      info = details["tripadvisor"]
      reviews = info.get("reviews", [])
      firstReview = ""
      if len(reviews) > 0:
          firstReview = reviews[0]["text"]

      try:
          providers["tripAdvisor"] = {
            "rating"          : float(info["rating"]) if info["rating"] else None, # This is the aggregate rating, and can be empty
            "totalReviewCount": int(info["num_reviews"]),
            "description"     : firstReview, # The rating of this review is not included
            "url"             : info["web_url"]
          }
      except KeyError:
          log.debug("TripAdvisor weird for " + biz.id)

    # Foursquare
    if "foursquare" in details:
      info = details["foursquare"]
      providers["foursquare"] = {
        "images": _imageRecords(info["images"], info["url"])
      }

    # Factual Places
    if "factual" in details:
      info = details["factual"]
      providers["factual"] = {
        "url": info.get("website", None)
      }

    return {
      "providers": providers
    }

def _imageRecords(imageURLs, onClick):
    # First iteration, such that there is only one page
    # to go to if the user taps on the page.
    return [
      {
        "src"        : url,
        "providerURL": onClick,
      }
      for url in imageURLs
      if url.split(".")[-1] in ["jpg", "jpeg", "png"]
    ]

def _yelpTimeFormat(string):
    try:
      from datetime import datetime
      dt = datetime.strptime(string, "%H%M")
      return dt.strftime("%H:%M")
    except ValueError:
      return string

def _yelpHoursRecord(hours):
    # "hours": [
    #   {
    #     "hours_type": "REGULAR", 
    #     "open": [
    #       {
    #         "start": "1000", 
    #         "end": "2300", 
    #         "day": 0, 
    #         "is_overnight": false
    #       }, 
    #   }
    # ]
    # https://www.yelp.com/developers/documentation/v3/business
    if hours is None:
        return []
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    record = {}
    for day in days:
        record[day] = []
    for section in hours:
        for dayTime in section.get("open", []):
            day = days[dayTime["day"]]
            record[day].append([
              _yelpTimeFormat(dayTime["start"]),
              _yelpTimeFormat(dayTime["end"]),
            ])
    return record

def eventRecord(yelpId, lat, lon, title, startTime, endTime, url):
    # backward-compatible usage of local*Time
    try :
        isoStartTime = parser.parse(startTime)
    except TypeError:
        # No start time
        return None

    if not isSingleDayEvent(startTime, endTime):
        # Don't show ongoing events that span more than a day
        return None

    isoEndTime = parser.parse(endTime) if endTime else isoStartTime + datetime.timedelta(hours=1)

    r = {
            "id": hashlib.md5(title[:30] + startTime).hexdigest(),
            "placeId": yelpId,
            # We cast to string, because that's what the app is expecting, 
            # not because it is right.
            "coordinates": { "lat": str(lat), "lng": str(lon) },
            "description": title,
            "localStartTime": isoStartTime.replace(tzinfo=None, second=1).isoformat(),
            "localEndTime": isoEndTime.replace(tzinfo=None, second=1).isoformat(),
            "utcStartTime": startTime,
            "utcEndTime": endTime,
            "url": url
    }
    return r

def createEventKey(eventObj):
    return eventObj['id']

def createKey(biz):
    return biz.id

def geoRecord(biz):
    return geoRecordFromCoord(biz.location.coordinate.latitude, biz.location.coordinate.longitude)

def geoRecordFromCoord(lat, lon):
    import pygeohash as pgh
    return {
       "g": pgh.encode(lat, lon, precision=8),
       "l": [lat, lon]
    }

# This maps a provider name to a number (where 1 means fetched, 0 means that
# place doesn't exist in that provider, and null means we haven't attempted to
# fetch the place from that provider yet). This will allow us to incrementally
# add multiple sources to the base Yelp results.
def baseStatus(biz):
    return {
      "yelp": 1,
      "identifiers": {
        "name": biz.name,
        "lat": biz.location.coordinate.latitude,
        "lng": biz.location.coordinate.longitude
      }
    }
