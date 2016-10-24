def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API
    providers = {}
    images = []
    hours = []
    if "yelp" in details:
      info = details["yelp"]
      providers["yelp"] = {
        "rating": biz.rating,
        "reviewCount": biz.review_count,
        "ratingMax": 5,
        "description": biz.snippet_text,
        "url": biz.url
      }
      images = images + info["photos"]
      hours = info["hours"][0]["open"]

    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url": info.url,
        "description": info.summary
      }
      images = images + info.images

    return {
      "id": biz.id,
      "name": biz.name,
      "hours": hours,
      "coordinates": {
        "lat": biz.location.coordinate.latitude,
        "lng": biz.location.coordinate.longitude
      },
      "images": images,
      "address": biz.location.display_address,
      "description": biz.snippet_text,
      "providers": providers,
      "version": 1.0
    }

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
