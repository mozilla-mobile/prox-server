def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API
    return {
      "version": 1.0,
      "id": biz.id,

      "name": "A Temporary Name",
      "summary": biz.snippet_text,
      "coordinates": {
        "lat": biz.location.coordinate.latitude,
        "long": biz.location.coordinate.longitude
      },

      "categories": ["Temporary Hotel"],
      "url": "http://mozilla.org",

      "address": biz.location.display_address,

      "providers": {
        "yelp": {
          "rating": biz.rating,
          "totalReviewCount": biz.review_count,
          "url": biz.url,
          "reviews": ["Yelp temp review"]
        },
        "tripAdvisor": {
          "rating": 1.0,
          "totalReviewCount": 1337,
          "url": "http://http://tripadvisor.com/",
          "reviews": ["TripAdvisor temp review"]
        }
      },

      "photoURLs": []

      # TODO: hours
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
