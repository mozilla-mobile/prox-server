from app.util import log

def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API

    from collections import OrderedDict
    # h is derived from the providers, but for the main body of the record.
    # h is for header.
    h = {
      "url"        : "https://mozilla.org",
      "description": {},
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
      h["images"]      += info["photos"]
      h["hours"]       = _yelpHoursRecord(info["hours"])
      h["description"] = _descriptionRecord("yelp", biz.snippet_text)
      h["categories"].update([ (c["title"], _categoryRecord(c["alias"], c["title"])) for c in info["categories"] if "title" in c])


    # Wikipedia.
    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url"        : info.url,
        "description": info.summary
      }
      h["description"] = _descriptionRecord("wikipedia", info.summary)
      h["images"]     += info.images

    # Ensure we're not getting SVG or other weird formats.
    h["images"] = [url for url in h["images"] if url.split(".")[-1] in ["jpg", "jpeg", "png"]]

    return {
      "version"    : 1,
      "id"         : biz.id,
      
      "name"       : biz.name,
      "description": h["description"],
      
      "url"        : h["url"],
      "phone"      : biz.display_phone,
      
      "address"    : biz.location.display_address,
      "coordinates": {
        "lat": biz.location.coordinate.latitude,
        "lng": biz.location.coordinate.longitude
      },

      "categories" : h["categories"].values(),
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
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    record = {}
    for day in days:
        record[day] = []
    for section in hours:
        for dayTime in section["open"]:
            day = days[dayTime["day"]]
            record[day] += [
              _yelpTimeFormat(dayTime["start"]),
              _yelpTimeFormat(dayTime["end"]),
            ]
    return record

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