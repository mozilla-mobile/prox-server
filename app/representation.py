import random

def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API

    from collections import OrderedDict
    # h is derived from the providers, but for the main body of the record.
    # h is for header.
    h = {
      "url"        : "https://mozilla.org",
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
      h["categories"].update([ (c["title"], _categoryRecord(c["alias"], c["title"])) for c in info["categories"] if "title" in c])
      h["images"]     += _imageRecords("yelp", info.get("photos", []), biz.url)
      h["hours"]       = _yelpHoursRecord(info["hours"])


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
      reviews = info["reviews"]
      firstReview = ""
      if len(reviews) > 0:
          firstReview = reviews[0]["text"]
          h["description"].append(_descriptionRecord("tripadvisor", firstReview))

      providers["tripAdvisor"] = {
        "rating"          : float(info["rating"]), # This is the aggregate rating
        "totalReviewCount": int(info["num_reviews"]),
        "description"     : firstReview, # The rating of this review is not included
        "url"             : info["web_url"]
      }

    # Foursquare
    if "foursquare" in details:
        info = details["foursquare"]
        h["images"] += _imageRecords("foursquare", info["images"], info["url"])

    images = h["images"]
    h["images"] = random.sample(images, len(images))

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

def eventRecord(yelpId, lat, lon, title, startTime, url):
    return {
            "id": yelpId,
            "coordinates": { "lat": lat, "lng": lon },
            "description": title,
            "startTime": startTime,
            "url": url
    }

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
