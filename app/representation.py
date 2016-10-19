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

      "photoURLs": [],

      # Format: <day>: { "start"/"end": <24h-time> }
      #
      # Notes:
      #   - <day> = 0 for Monday
      #   - <24h-time>, e.g. 1400 for 2pm
      #   - Times are in the timezone of the location
      #   - "end" < "start" if a location is open overnight
      #   - An entry for <day> will be missing if a location is not open that day
      "hours": {
        0: {
          "start": 1400,
          "end": 1830
        },
        4: {
          "start": 1400,
          "end": 200
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
