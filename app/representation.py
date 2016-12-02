import random
from dateutil import parser
import datetime
from app.util import log
from events import isSingleDayEvent
import uuid

import json

def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API

    from collections import OrderedDict
    # h is derived from the providers, but for the main body of the record.
    # h is for header.
    h = {
      "url"        : None,
      "description": [],
      "categories" : OrderedDict(),
      "images"     : [],
      "hours"      : [],
    }
    providers = {}
    
    # Yelp.
    if "yelp" in details:
      info = details["yelp"]
      providers["yelp"] = {
        "rating"          : biz.rating,
        "totalReviewCount": biz.review_count,
        "ratingMax"       : 5,
        "description"     : biz.snippet_text,
        "url"             : biz.url
      }
      h["description"].append(_descriptionRecord("yelp", biz.snippet_text))
      if "categories" in info:
          h["categories"].update([
            (c["title"], _categoryRecord(c["alias"], c["title"])) 
            for c in info["categories"] 
            if "title" in c
          ])
      h["images"]     += _imageRecords("yelp", info.get("photos", []), biz.url)
      h["hours"]       = _yelpHoursRecord(info.get("hours", None))


    # Wikipedia.
    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url"        : info["url"],
        "description": info["summary"]
      }
      h["description"].append(_descriptionRecord("wikipedia", info["summary"]))
      h["images"]     += _imageRecords("wikipedia", info["images"], info["url"])

    # TripAdvisor
    if "tripadvisor" in details:
      info = details["tripadvisor"]
      reviews = info.get("reviews", [])
      firstReview = ""
      if len(reviews) > 0:
          firstReview = reviews[0]["text"]
          h["description"].append(_descriptionRecord("tripadvisor", firstReview))

      try:
          providers["tripAdvisor"] = {
            "rating"          : float(info["rating"]), # This is the aggregate rating
            "totalReviewCount": int(info["num_reviews"]),
            "description"     : firstReview, # The rating of this review is not included
            "url"             : info["web_url"]
          }
      except KeyError:
          log.debug("TripAdvisor weird for " + biz.id)


    # Foursquare
    if "foursquare" in details:
        info = details["foursquare"]
        h["images"] += _imageRecords("foursquare", info["images"], info["url"])

    # Factual Places
    if "factual" in details:
        info = details["factual"]
        h["url"] = info.get("website", None)

    images = h["images"]
    h["images"] = random.sample(images, len(images))
    coord = None
    if biz.location is not None and biz.location.coordinate is not None:
        coord = {
          "lat": biz.location.coordinate.latitude,
          "lng": biz.location.coordinate.longitude
        }
    return {
      "version"    : 1,
      "id"         : biz.id,
      
      "name"       : biz.name,
      "description": h["description"],
      
      "url"        : h["url"],
      "phone"      : biz.display_phone,
      
      "address"    : biz.location.display_address,
      "coordinates": coord,

      "categories" : list(h["categories"].values()),
      "providers"  : providers,
      
      "images"     : h["images"],
      "hours"      : h["hours"],
    }

def _categoryRecord(id, text):
    return {
      "id"  : id,
      "text": text,
    }

def _descriptionRecord(provider, text, url = None):
    return {
      "text"    : text,
      "provider": provider,
    }

def _imageRecords(provider, imageURLs, onClick):
    # First iteration, such that there is only one page
    # to go to if the user taps on the page.
    return [
      {
        "src"        : url,
        "provider"   : provider,
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
            "id": str(uuid.uuid4()),
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
    return _geoRecord(biz.location.coordinate.latitude, biz.location.coordinate.longitude)

def _geoRecord(lat, lon):
    import pygeohash as pgh
    return {
       "g": pgh.encode(lat, lon, precision=8),
       "l": [lat, lon]
    }
