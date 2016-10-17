  # biz is the response object from the Yelp Search API
  return {
    "version": 1.0,
    "id": biz.id,
    "geo": {
      "lat": biz.location.coordinate.latitude,
      "lon": biz.location.coordinate.longitude
    },
    "images": [],
    "address": biz.location.display_address,
def venueRecord(biz, **details):

    "pullQuote": biz.snippet_text,

    "providers": {
      "yelp": {
        "rating": biz.rating,
        "reviewCount": biz.review_count,
        "ratingMax": 5,
        "url": biz.url
      }
    }
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